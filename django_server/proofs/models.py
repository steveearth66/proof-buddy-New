from django.db import models

TEMPLATE_CHOICES = [
    ('ER', 'ER'),
    ('MP', 'MP'),
    ('MT', 'MT'),
    ('DS', 'DS'),
    ('ADD', 'ADD'),
]


class Proof(models.Model):
    name = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)
    lsh = models.CharField(max_length=100, blank=True)
    rsh = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        'accounts.Account', related_name='proofs', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    isComplete = models.BooleanField(default=False)
    template = models.CharField(
        max_length=3, choices=TEMPLATE_CHOICES, default='ER')

    def __str__(self):
        return self.name


class ProofLine(models.Model):
    proof = models.ForeignKey(
        Proof, related_name='proof_lines', on_delete=models.CASCADE)
    left_side = models.BooleanField(default=True)
    racket = models.CharField(max_length=255)
    rule = models.CharField(max_length=100)
    start_position = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    errors = models.TextField(default='')

    def __str__(self):
        return self.racket

    def get_proof_tag(self):
        return self.proof.tag


class Definition(models.Model):
    label = models.CharField(max_length=100)
    def_type = models.CharField(max_length=100)
    expression = models.CharField(max_length=255)
    notes = models.TextField(default='')
    proof = models.ForeignKey(
        Proof, related_name='definitions', on_delete=models.CASCADE, null=True)
    created_by = models.ForeignKey(
        'accounts.Account', related_name='definitions', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_tag(self):
        return self.proof.tag
