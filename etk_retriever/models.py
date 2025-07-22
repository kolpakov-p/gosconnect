from django.db import models


class Credentials(models.Model):
    login = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.login


class RetrieveRequests(models.Model):
    text = models.TextField()
    received_at = models.DateTimeField()
    credentials = models.ForeignKey(Credentials, on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RetrieveRequest {self.id}: {self.text[:20]}..."


class CaptchaSolving(models.Model):
    session_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    credentials = models.ForeignKey(Credentials, on_delete=models.RESTRICT)
    img_url = models.TextField()
    solved_text = models.TextField()
    is_solved = models.BooleanField(default=False)

    def __str__(self):
        return f"CaptchaSolving {self.id}: {self.solved_text[:20]}..."


class SecondFactorRequest(models.Model):
    session_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    credentials = models.ForeignKey(Credentials, on_delete=models.RESTRICT)
    second_factor = models.TextField()
    is_captured = models.BooleanField(default=False)

    def __str__(self):
        return f"CaptchaSolving {self.id}: {self.second_factor[:20]}..."
