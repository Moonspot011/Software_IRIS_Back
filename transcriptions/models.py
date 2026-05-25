from django.db import models

class TranscriptionSession(models.Model):
    """Sesión de transcripción en tiempo real."""
    teacher_uid  = models.CharField(max_length=128, help_text="firebase_uid del docente")
    session_name = models.CharField(max_length=200, blank=True, default='')
    transcript   = models.TextField(blank=True)
    highlighted_transcript = models.TextField(blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sesión de Transcripción'

    def __str__(self):
        return f"{self.session_name or 'Sin nombre'} — {self.created_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        # Solo procesar si el texto cambió o si es nuevo y no está vacío
        is_new = self.pk is None
        should_process = False

        if is_new:
            if self.transcript:
                should_process = True
        else:
            try:
                orig = TranscriptionSession.objects.get(pk=self.pk)
                if orig.transcript != self.transcript or (self.transcript and not self.highlighted_transcript):
                    should_process = True
            except TranscriptionSession.DoesNotExist:
                if self.transcript:
                    should_process = True

        if should_process:
            from .services import highlight_concepts_with_gemini, get_next_reset_time_bogota
            from google.genai.errors import APIError

            try:
                self.highlighted_transcript = highlight_concepts_with_gemini(self.transcript)
            except APIError as e:
                if e.code == 429:
                    error_msg = str(e.message).lower()
                    if "daily" in error_msg or "per day" in error_msg:
                        reset_time = get_next_reset_time_bogota()
                        self.highlighted_transcript = (
                            f"Se acabaron los tokens gratuitos diarios para resaltar conceptos. "
                            f"Volverá a estar disponible aproximadamente a las {reset_time}."
                        )
                    else:
                        self.highlighted_transcript = (
                            "Se superó el límite de peticiones por minuto para resaltar conceptos. "
                            "Por favor, espera 1 minuto e intenta de nuevo."
                        )
                else:
                    self.highlighted_transcript = f"Error en la API de Gemini (Código {e.code}): {e.message}"
            except Exception as e:
                self.highlighted_transcript = f"No se pudieron resaltar los conceptos en este momento: {str(e)}"

        super().save(*args, **kwargs)
