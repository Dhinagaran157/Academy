from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, FileExtensionValidator
from django.contrib.auth.models import User
import os
import uuid
from django.utils import timezone
from datetime import timedelta

# Custom image validator (shared across models)
def validate_image(image):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError("Only JPG, JPEG, PNG, WEBP, GIF files are allowed.")
    if image.size > 2 * 1024 * 1024:
        raise ValidationError("Image size must be under 2MB.")

class Messages(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    course = models.CharField(max_length=50)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

# Admission Model
class admission(models.Model):
    credentials_sent = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='student_avatars/', validators=[validate_image], null=True, blank=True)
    stu_id = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=100)  # Reduced from 255
    phone = models.CharField(max_length=15, validators=[RegexValidator(r'^\+?1?\d{9,15}$')])
    whatsapp = models.CharField(max_length=15, validators=[RegexValidator(r'^\+?1?\d{9,15}$')])
    email = models.EmailField(max_length=100, unique=True)  # Reduced from 150
    mode = models.CharField(max_length=10, choices=[
        ('online', 'Online'), ('offline', 'Offline'), ('hybrid', 'Hybrid')
    ])
    graduation_year = models.CharField(max_length=4, choices=[
        ('2022', '2022'), ('2023', '2023'), ('2024', '2024'), ('2025', '2025')
    ])
    course = models.CharField(max_length=50, choices=[  # Reduced from 100
        ('Python FSD', 'Python FSD'), ('Cloud Security', 'Cloud Security'),
        ('AI', 'AI'), ('Data Analysis', 'Data Analysis'), ('Software Testing', 'Software Testing')
    ])
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.stu_id:
            self.stu_id = "STU" + str(uuid.uuid4().hex[:6]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.course}"

# Staff Model
class Staff(models.Model):
    DEPARTMENT_CHOICES = [
        ('Python FSD', 'Python FSD'), ('Cloud Security', 'Cloud Security'),
        ('AI', 'AI'), ('Data Analysis', 'Data Analysis'), ('Software Testing', 'Software Testing')
    ]
    credentials_sent = models.BooleanField(default=False)
    staff_id = models.CharField(max_length=20, unique=True, editable=False)
    first_name = models.CharField(max_length=50)  # Reduced
    last_name = models.CharField(max_length=50)   # Reduced
    email = models.EmailField(max_length=100, unique=True)  # Reduced
    phone = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=128)
    image = models.ImageField(upload_to='staff_images/', validators=[validate_image], null=True, blank=True)
    departments = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)  # Reduced
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.staff_id:
            self.staff_id = "STF" + str(uuid.uuid4().hex[:6]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Course Model
class Course(models.Model):
    course_id = models.CharField(max_length=20, unique=True, editable=False)
    course_name = models.CharField(max_length=100)  # Reduced from 200
    description = models.TextField()
    duration = models.FloatField(default=0)
    pro_duration = models.CharField(max_length=50, default="")  # Reduced
    total_duration = models.CharField(max_length=50, default="")  # Reduced
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='course_images/', validators=[validate_image], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.course_id:
            self.course_id = "COU" + str(uuid.uuid4().hex[:6]).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.course_name


# Class Notes
class ClassNote(models.Model):
    DEPARTMENT_CHOICES = [
        ('Python FSD', 'Python FSD'), ('Cloud Security', 'Cloud Security'),
        ('AI', 'AI'), ('Data Analysis', 'Data Analysis'), ('Software Testing', 'Software Testing')
    ]
    VISIBILITY_CHOICES = [('all', 'All'), ('batch', 'Batch')]
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    topic = models.CharField(max_length=100)  # Reduced from 200
    file = models.FileField(upload_to='notes/%Y/%m/%d/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])])
    description = models.TextField(blank=True, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='all')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['department', '-uploaded_at'])]

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.topic} - {self.department}"

# Syllabus
class Syllabus(models.Model):
    course = models.CharField(max_length=100)
    topic = models.CharField(max_length=200)
    syllabus_file = models.FileField(upload_to='syllabus/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.course

    class Meta:
        ordering = ['-created_at']

# Certificate
class Certificate(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('issued', 'Issued'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    stu_id = models.CharField(max_length=20)
    student_name = models.CharField(max_length=100)
    certified_course = models.CharField(max_length=200)
    batch = models.CharField(max_length=20)
    issued_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    certificate_file = models.FileField(
        upload_to='certificates/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg'])]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cert_id = models.CharField(max_length=30, unique=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if not self.cert_id:
            self.cert_id = f"AER-CERT-{timezone.now().year}-{self.stu_id.split('-')[-1].zfill(3)}"
        if not self.expiry_date:
            self.expiry_date = self.issued_date + timedelta(days=730)  # 2 years
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_name} - {self.certified_course}"

# Gallery
class Gallery(models.Model):
    CATEGORY_CHOICES = [
        ('training_sessions', 'Training Sessions'),
        ('project_demo', 'Project Demonstrations'),
        ('interview', 'Interview'),
        ('certification', 'Certification Programs'),
        ('placement_drive', 'Placement Drives'),
        ('seminar', 'Tech Seminars & Webinars'),
    ]
    MEDIA_TYPE = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/images/', blank=True, null=True, validators=[validate_image])
    video = models.FileField(upload_to='gallery/videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class GalleryImage(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='gallery/', validators=[validate_image])

# Attendance
class Attendance(models.Model):
    student = models.ForeignKey(admission, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[("Present", "Present"), ("Absent", "Absent")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"
#============== Notification =================
class NotificationPreference(models.Model):
    email = models.BooleanField(default=True)
    sms = models.BooleanField(default=False)
    app = models.BooleanField(default=True)

    def __str__(self):
        return "Notification Preferences"