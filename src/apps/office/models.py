from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
import datetime

User = get_user_model()

class Letter(models.Model):
    LETTER_TYPES = [
        ('to_officials', 'To Officials'),
        ('certificate_generation', 'Certificate Generation'),
    ]

    letter_number = models.CharField(max_length=20, unique=True, editable=False)
    letter_type = models.CharField(max_length=30, choices=LETTER_TYPES, help_text="Type of Letter")
    letter_content = models.JSONField(help_text="Letter content in JSON format")
    issued_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="letters_issued")
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.letter_number} - {self.letter_type}"

    class Meta:
        ordering = ['-issued_at']
        verbose_name = "Letter"
        verbose_name_plural = "Letters"

# Auto-generate letter_number in the format: LTR-YYYYMMDD-XXXX
@receiver(pre_save, sender=Letter)
def generate_letter_number(sender, instance, **kwargs):
    if not instance.letter_number:
        today = datetime.date.today().strftime("%Y%m%d")
        latest_letter = Letter.objects.filter(letter_number__startswith=f"LTR-{today}").order_by('-letter_number').first()
        if latest_letter:
            last_number = int(latest_letter.letter_number.split("-")[-1]) + 1
        else:
            last_number = 1
        instance.letter_number = f"LTR-{today}-{last_number:04d}"