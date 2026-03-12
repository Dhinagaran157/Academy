from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from .models import Messages, Course, Gallery ,Certificate,Syllabus,Attendance
from django.contrib import messages
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.conf import settings
from .models import Gallery, GalleryImage,admission
import re,os
from django.utils import timezone
from .models import Staff
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import logging
from django.conf import settings 
from django.core.mail import send_mail
from .models import ClassNote
from django.http import FileResponse
from django.core.paginator import Paginator
import csv
from django.db.models import Q
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.views.decorators.http import require_POST
import json
from django.views.decorators.cache import never_cache
from functools import wraps
from PIL import Image
from datetime import date


# ================= NO CACHE DECORATOR =================
def no_cache(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    return wrapper


# ================= LOGIN VIEW =================
@never_cache
def login_view(request):

    if request.method == "POST":

        user_type = request.POST.get("user_type")
        email = request.POST.get("username")
        password = request.POST.get("password")

        # ================= STUDENT LOGIN =================
        if user_type == "student":
            try:
                student = admission.objects.get(email=email)

                if student.stu_id == password:
                    request.session["user_type"] = "student"
                    request.session["stu_id"] = student.stu_id
                    request.session["student_name"] = student.full_name

                    return redirect("student_details")

                else:
                    messages.error(request, "Invalid Student ID")

            except admission.DoesNotExist:
                messages.error(request, "Student not found")


        # ================= STAFF LOGIN =================
        elif user_type == "staff":
            try:
                staff = Staff.objects.get(email=email)

                if staff.staff_id == password:

                    request.session["user_type"] = "staff"
                    request.session["staff_id"] = staff.staff_id
                    request.session["staff_name"] = staff.first_name

                    return redirect("staff")

                else:
                    messages.error(request, "Invalid Staff ID")

            except Staff.DoesNotExist:
                messages.error(request, "Staff not found")


        # ================= ADMIN LOGIN =================
        elif user_type == "admin":

            ADMIN_EMAIL = "admin@aerovant.com"
            ADMIN_PASSWORD = "Admin@123"

            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                request.session["user_type"] = "admin"
                return redirect("admin_dashboard")

            else:
                messages.error(request, "Invalid Admin Credentials")

    return render(request, "login.html")


# ================= STUDENT DASHBOARD =================
@no_cache
def student_dashboard(request):

    if request.session.get("user_type") != "student":
        return redirect("login")

    stu_id = request.session.get("stu_id")

    student = get_object_or_404(admission, stu_id=stu_id)

    context = {
        "student": student
    }

    return render(request, "student_details.html", context)


# ================= STAFF DASHBOARD =================
@no_cache
def staff_dashboard(request):

    if request.session.get("user_type") != "staff":
        return redirect("login")

    staff_id = request.session.get("staff_id")

    staff = get_object_or_404(Staff, staff_id=staff_id)

     # Courses handled
    courses = Course.objects.filter(staff=staff)

    # Notes
    notes = ClassNote.objects.all().order_by("-uploaded_at")

    # Syllabus
    syllabus_list = Syllabus.objects.all()

    # Total students in department
    total_stu = admission.objects.filter(department=staff.department).count()

    context = {
        "staff": staff,
        "courses": courses,
        "notes": notes,
        "syllabus_list": syllabus_list,
        "total_stu": total_stu
    }
    
    

    return render(request, "staff.html", context)


# ================= ADMIN DASHBOARD =================
@no_cache
def admin_dashboard(request):

    if request.session.get("user_type") != "admin":
        return redirect("login")

    return render(request, "dashboard.html")


# ================= LOGOUT =================
@never_cache
def logout_view(request):

    request.session.flush()

    return redirect("login")
#----=====================================================

def home(request):
    
    return render(request, "index.html")


def about(request):
    return render(request,"about.html")
#======================= Staff and student details viewer =======================


@never_cache
def staff(request):

    # 🔐 Security Check
    if request.session.get("user_type") != "staff":
        return redirect("login")

    staff_id = request.session.get("staff_id")

    try:
        # ================= STAFF PROFILE =================
        staff = Staff.objects.get(staff_id=staff_id)

        # ================= DEPARTMENTS =================
        departments = staff.departments.split(",")

        # Count departments
        dept_count = len(departments)

        # ================= STUDENTS =================
        students = admission.objects.filter(course__in=departments)

        total_students = students.count()

        # ================= TODAY ATTENDANCE =================
        attendance = Attendance.objects.filter(
            student__in=students,
            date=date.today()
        )
        notes = ClassNote.objects.filter(department__in=departments)
        syllabus_list = Syllabus.objects.filter(course__in=departments)

    except Staff.DoesNotExist:
        return redirect("login")

    context = {
        "staff": staff,
        "departments": departments,
        "dept_count": dept_count,
        "students": students,
        "total_students": total_students,
        "attendance": attendance,
        'notes':notes,
        "syllabus_list":syllabus_list
    }

    return render(request, "staff.html", context)

#==============Staff logic =====================

def staff_register(request):

    query = request.GET.get("q", "").strip()

    all_staff = Staff.objects.all().order_by("-created_at")

    # 🔎 SEARCH
    if query:
        all_staff = all_staff.filter(
            Q(staff_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(departments__icontains=query)
        )

    # =========================
    # ➕ ADD STAFF
    # =========================
    if request.method == "POST" and "add_staff" in request.POST:

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        image = request.FILES.get("image")
        departments = request.POST.getlist("departments")
        

        if not all([first_name, last_name, email, password, departments]):
            messages.error(request, "All required fields must be filled!")
            return redirect("staff_register")

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            messages.error(request, "Invalid email format!")
            return redirect("staff_register")

        if Staff.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect("staff_register")

        if phone and not re.match(r'^[6-9]\d{9}$', phone):
            messages.error(request, "Enter valid 10-digit phone number!")
            return redirect("staff_register")

        if password != password2:
            messages.error(request, "Passwords do not match!")
            return redirect("staff_register")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters!")
            return redirect("staff_register")


        Staff.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            password=make_password(password),
            image=image,
            credentials_sent=False,
            departments=",".join(departments)
        )

        messages.success(request, "Staff added successfully!")
        return redirect("staff_register")

    # =========================
    # 📧 SEND CREDENTIALS
    # =========================
    if request.method == "POST" and "send_credentials" in request.POST:

        staff_id = request.POST.get("staff_id")
        staff = get_object_or_404(Staff, id=staff_id)

        subject = "Your Staff Account Credentials"

        message = f"""
Hello {staff.first_name},

Your login credentials:

Username: {staff.email}
Password: {staff.staff_id}

Please login useing those credential .

Regards,
Admin Team
"""

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [staff.email],
            fail_silently=False,
        )

        staff.credentials_sent = True
        staff.save()

        messages.success(request, "Credentials sent successfully!")
        return redirect("staff_register")

    # =========================
    # ✏️ UPDATE STAFF
    # =========================
    if request.method == "POST" and "update_staff" in request.POST:

        staff_id = request.POST.get("staff_id")
        staff = get_object_or_404(Staff, id=staff_id)

        staff.first_name = request.POST.get("first_name", "").strip()
        staff.last_name = request.POST.get("last_name", "").strip()
        staff.email = request.POST.get("email", "").strip()
        staff.phone = request.POST.get("phone", "").strip()
        departments = request.POST.getlist("departments")
        staff.departments = ",".join(departments)
        staff.save()

        messages.success(request, "Staff updated successfully!")
        return redirect("staff_register")

    # =========================
    # ❌ DELETE STAFF
    # =========================
    if request.method == "POST" and "delete_staff" in request.POST:

        staff_id = request.POST.get("staff_id")
        staff = get_object_or_404(Staff, id=staff_id)
        staff.delete()

        messages.success(request, "Staff deleted successfully!")
        return redirect("staff_register")

    # =========================
    # ❌ DELETE ALL STAFF
    # =========================
    if request.method == "POST" and "delete_all" in request.POST:

        Staff.objects.all().delete()
        messages.success(request, "All staff deleted successfully!")
        return redirect("staff_register")

    # =========================
    # ❌ BULK DELETE
    # =========================
    if request.method == "POST" and "bulk_delete" in request.POST:

        selected_ids = request.POST.getlist("selected_ids")

        if selected_ids:
            Staff.objects.filter(id__in=selected_ids).delete()
            messages.success(request, "Selected staff deleted successfully!")
        else:
            messages.warning(request, "No staff selected!")

        return redirect("staff_register")

    # =========================
    # 📊 CONTEXT DATA
    # =========================
    context = {
        "all_staff": all_staff,
        "query": query,
        "total_staff": all_staff.count(),
    }

    return render(request, "dashboard/staff_register.html", context)
#========================== Staff csv file =====================
def export_staff(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="staff.csv"'

    writer = csv.writer(response)

    # Header Row
    writer.writerow([
        "ID",
        "Staff ID",
        "First Name",
        "Last Name",
        "Email",
        "Phone",
        "Department",
        "Created Date"
    ])

    staff_members = Staff.objects.all().order_by("-created_at")

    for staff in staff_members:
        writer.writerow([
            staff.id,
            staff.staff_id,
            staff.first_name,
            staff.last_name,
            staff.email,
            staff.phone,
            staff.departments,
            staff.created_at
        ])

    return response
# ================= STAFF DASHBOARD =================
#========================= Staff upload notes====================


# ================= NOTES UPLOAD =================
def upload_notes_staff(request):

    if request.method == "POST":

        department = request.POST.get("department")
        topic = request.POST.get("topic")
        file = request.FILES.get("file")
        description = request.POST.get("description")
        visibility = request.POST.get("visibility")

        ClassNote.objects.create(
            department=department,
            topic=topic,
            file=file,
            description=description,
            visibility=visibility
        )

        messages.success(request, "Notes uploaded successfully!")

        return redirect("/staff/#upload-notes")


# ================= EDIT NOTE =================
def edit_note(request, id):

    note = get_object_or_404(ClassNote, id=id)

    if request.method == "POST":

        note.department = request.POST.get("department")
        note.topic = request.POST.get("topic")
        note.description = request.POST.get("description")
        note.visibility = request.POST.get("visibility")

        if request.FILES.get("file"):
            note.file = request.FILES.get("file")

        note.save()

        messages.success(request, "Note updated successfully!")

        return redirect("/staff/#upload-notes")

    context = {
        "note": note
    }

    return render(request, "edit_note.html", context)


# ================= DELETE NOTE =================
def delete_note(request, id):

    note = get_object_or_404(ClassNote, id=id)

    note.delete()

    messages.success(request, "Note deleted successfully!")

    return redirect("/staff/#upload-notes")


# ================= SYLLABUS UPLOAD =================
def upload_syllabus(request):

    if request.method == "POST":

        course = request.POST.get("course")
        topic = request.POST.get("topic")
        syllabus_file = request.FILES.get("syllabus_file")

        Syllabus.objects.create(
            course=course,
            topic=topic,
            syllabus_file=syllabus_file
        )

        messages.success(request, "Syllabus uploaded successfully!")

        return redirect("/staff/#upload-syllabus")

#=================== Update syllabus ==========================

def edit_syllabus(request, id):

    syllabus = get_object_or_404(Syllabus, id=id)

    if request.method == "POST":

        syllabus.course = request.POST.get("course")
        syllabus.topic = request.POST.get("topic")

        if request.FILES.get("syllabus_file"):
            syllabus.syllabus_file = request.FILES.get("syllabus_file")

        syllabus.save()

        messages.success(request, "Syllabus updated successfully!")

        return redirect("/staff/#upload-syllabus")

    return redirect("/staff/#upload-syllabus")

#==================== Delete Syllabus =======================

def delete_syllabus(request, id):

    syllabus = get_object_or_404(Syllabus, id=id)
    syllabus.delete()

    messages.success(request, "Syllabus deleted successfully!")

    return redirect("/staff/#upload-syllabus")    



#-------------------------------------------------------------------------

def dashboard(request):
    total_courses = Course.objects.count()
    total_enquiries = Messages.objects.count()
    total_images=Gallery.objects.count() 
    total_students=admission.objects.count()
    # 👈 Added this line

    return render(request, 'dashboard/dashboard.html', {
        'total_courses': total_courses,
        'total_enquiries': total_enquiries,  
        'total_images':total_images,
        'total_students':total_students,# 👈 Send to template
        
    })


def Messages_details(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        course = request.POST.get('course', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Check all fields filled
        if not all([full_name, email, phone, course, message]):
            messages.error(request, 'Please fill all required fields correctly.')
            return redirect('/home#contact')
        
        # Email validation
        if '@' not in email or '.' not in email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            messages.error(request, 'Please enter a valid email address.')
            return redirect('/home#contact')
        
        # Phone validation - FIXED
        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) != 10 or phone_digits[0] not in '6789':
            messages.error(request, 'Enter valid 10-digit mobile (starts with 6-9)')
            return redirect('/home#contact')
        
        # Save data
        Messages.objects.create(
            full_name=full_name,
            email=email,
            phone=phone_digits,  # Store clean digits only
            course=course,
            message=message
        )
        messages.success(request, 'Thank you! We will contact you within 24 hours.')
        return redirect('/home#contact')
    
    return render(request, 'index.html')

def Enquiry_View(request):
    details = Messages.objects.all()
    return render(request, 'dashboard/enquiry_list.html', {'data': details})


def course_details(request):

    # ================= ADD COURSE =================
    if request.method == "POST" and 'add_course' in request.POST:
        Course.objects.create(
            course_name=request.POST.get('course_name'),
            description=request.POST.get('description'),
            duration=float(request.POST.get('duration') or 0),
            pro_duration=float(request.POST.get('pro_duration') or 0),
            total_duration=float(request.POST.get('total_duration') or 0),
            price=request.POST.get('price'),
            discount_price=request.POST.get('discount_price') or None,
            image=request.FILES.get('image')
        )
        return redirect('course_details')

    # ================= UPDATE COURSE =================
    if request.method == "POST" and 'update_course' in request.POST:
        course = get_object_or_404(Course, id=request.POST.get('id'))

        course.course_name = request.POST.get('course_name')
        course.description = request.POST.get('description')
        course.duration = float(request.POST.get('duration') or 0)
        course.pro_duration = float(request.POST.get('pro_duration') or 0)
        course.total_duration = float(request.POST.get('total_duration') or 0)
        course.price = request.POST.get('price')
        course.discount_price = request.POST.get('discount_price') or None

        if request.FILES.get('image'):
            course.image = request.FILES.get('image')

        course.save()
        return redirect('course_details')

    # ================= DELETE COURSE =================
    if request.method == "POST" and 'delete_course' in request.POST:
        course = get_object_or_404(Course, id=request.POST.get('id'))
        course.delete()
        return redirect('course_details')

    # ================= CONTEXT =================
    courses = Course.objects.all().order_by('-id')
    total_courses = courses.count()
    total_price = sum(course.price for course in courses)

    context = {
        'courses': courses,
        'total_courses': total_courses,
        'total_price': total_price,
    }

    return render(request, 'dashboard/course_details.html', context)

#=================Student=========================

def student_details(request):

    # 🔐 Security Check
    if request.session.get("user_type") != "student":
        return redirect("login")

    stu_id = request.session.get("stu_id")

    try:
        # ================= PROFILE =================
        student = admission.objects.get(stu_id=stu_id)

        # ================= TOTAL STUDENTS =================
        total_students = admission.objects.count()

        # ================= COURSE =================
        course = Course.objects.filter(course_name=student.course).first()

        # ================= CERTIFICATES =================
        certificates = Certificate.objects.filter(stu_id=stu_id)

        # ================= CLASS NOTES =================
        notes = ClassNote.objects.filter(department=student.course)

        # ================= SYLLABUS =================
        syllabus = Syllabus.objects.filter(course=student.course)

    except admission.DoesNotExist:
        return redirect("login")

    context = {
        "student": student,
        "course": course,
        "certificates": certificates,
        "notes": notes,
        "syllabus_details": syllabus,
        "total_students": total_students
    }

    return render(request, "student_details.html", context)
#============================

def student_dashboard(request):
    stu_id = request.session.get('stu_id')   # logged student id
    
    certificates = Certificate.objects.filter(stu_id=stu_id)

    context = {
        'certificates': certificates
    }
    return render(request, 'student_dashboard.html', context)

def student_enroll(request):

    # 📧 SEND CREDENTIALS
    if request.method == "POST" and "send_credentials" in request.POST:
        student_id = request.POST.get("student_id")

        student = get_object_or_404(admission, id=student_id)

        subject = "Aerovant Academy - Student Account Created"

        message = f"""
Hello {student.full_name},

Welcome to Aerovant Academy.

Your student account has been successfully created.

Login Details
------------------------
Login URL : http://127.0.0.1:8000/student_login/
Username  : {student.email}
Password  : {student.stu_id}

For security reasons, please change your password after logging in.

If you face any issues, please contact the administrator.

Best Regards,
Aerovant Academy
Admin Team
"""

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [student.email],
            fail_silently=False,
        )

        student.credentials_sent = True
        student.save()

        messages.success(request, "Student credentials sent successfully.")
        return redirect("student_Enroll")


    # 🔍 SEARCH
    query = request.GET.get("q", "")
    students = admission.objects.all().order_by("-created_at")

    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(course__icontains=query)
        )

    # 📄 PAGINATION
    paginator = Paginator(students, 10)
    page_number = request.GET.get("page")
    students = paginator.get_page(page_number)

    context = {
        "students": students,
        "query": query
    }

    return render(request, "dashboard/students_Enroll.html", context)


def student_create(request):

    if request.method == "POST":

        email = request.POST.get("email")

        # Check email already exists
        if admission.objects.filter(email=email).exists():

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "status": "error",
                    "message": "This email is already registered."
                })

            messages.error(request, "⚠️ This email is already registered.")
            return redirect("home")

        # Save admission
        new_student = admission.objects.create(
            full_name=request.POST.get("full_name"),
            phone=request.POST.get("phone"),
            whatsapp=request.POST.get("whatsapp"),
            email=email,
            mode=request.POST.get("mode"),
            graduation_year=request.POST.get("graduation_year"),
            course=request.POST.get("course"),
            message=request.POST.get("message")
        )

        # 📢 Send Notification Email to Admin
        send_mail(
            subject="🚀 New Student Registration",
            message=f"""
A new student has registered.

Name: {new_student.full_name}
Email: {new_student.email}
Phone: {new_student.phone}
Course: {new_student.course}
Mode: {new_student.mode}


Message:
{new_student.message}
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=["humanresource@aerovanttech.com"],  # change to admin email
            fail_silently=True,
        )

        # AJAX response
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "success"})

        messages.success(request, "✅ Registration submitted successfully!")
        return redirect("home")

    return redirect("home")

def check_email(request):

    email = request.GET.get("email")

    if admission.objects.filter(email=email).exists():
        return JsonResponse({"status": "exists"})
    else:
        return JsonResponse({"status": "available"})
    
def view_stu(request):
    students = admission.objects.all()
    total_stu = students.count()

    context = {
        'students': students,
        'total_stu': total_stu
    }

    return render(request, 'dashboard/students_Enroll.html', context)

def student_edit(request, id):
    student = get_object_or_404(admission, id=id)

    if request.method == "POST":
        student.full_name = request.POST.get("full_name")
        student.phone = request.POST.get("phone")
        student.whatsapp = request.POST.get("whatsapp")
        student.email = request.POST.get("email")
        student.mode = request.POST.get("mode")
        student.graduation_year = request.POST.get("graduation_year")
        student.course = request.POST.get("course")
        student.message = request.POST.get("message")
        student.save()

        return redirect("student_Enroll")

    return render(request, "dashboard/students_Enroll.html", {"student": student})


def student_delete(request, id):
    student = get_object_or_404(admission, id=id)
    student.delete()
    return redirect("student_Enroll")

def export_students(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID", "Student ID", "Full Name", "Phone",
        "WhatsApp", "Email", "Mode",
        "Graduation Year", "Course", "Created Date"
    ])

    students = admission.objects.all()

    for student in students:
        writer.writerow([
            student.id,
            student.stu_id,
            student.full_name,
            student.phone,
            student.whatsapp,
            student.email,
            student.mode,
            student.graduation_year,
            student.course,
            student.created_at
        ])

    return response



#======================Upload nots=========================

def admission_management(request):
    return render(request,"dashboard/admission_management.html")


def site_settings(request):
    return render(request,"dashboard/settings.html")



#--------------Admission_details---------------

#------------Gallery_upload---------------------

def gallery_upload(request):

    if request.method == "POST":

        # ADD NEW GALLERY
        if "add_gallery" in request.POST:
            title = request.POST.get("title")
            category = request.POST.get("category")
            media_type = request.POST.get("media_type")
            description = request.POST.get("description", "")

            media_files = request.FILES.getlist("media_files")

            for media_file in media_files:
                Gallery.objects.create(
                    title=title,
                    category=category,
                    media_type=media_type,
                    description=description,
                    image=media_file if media_type == "image" else None,
                    video=media_file if media_type == "video" else None,
                )

        # UPDATE
        elif "update_gallery" in request.POST:
            gallery_id = request.POST.get("id")
            gallery = get_object_or_404(Gallery, id=gallery_id)

            gallery.title = request.POST.get("title")
            gallery.category = request.POST.get("category")
            gallery.media_type = request.POST.get("media_type")
            gallery.description = request.POST.get("description", "")

            media_files = request.FILES.getlist("media_files")

            if media_files:
                media_file = media_files[0]

                if gallery.media_type == "image":
                    gallery.image = media_file
                    gallery.video = None
                else:
                    gallery.video = media_file
                    gallery.image = None

            gallery.save()

        # DELETE
        elif "delete_gallery" in request.POST:
            gallery_id = request.POST.get("id")
            gallery = get_object_or_404(Gallery, id=gallery_id)
            gallery.delete()

        # BULK DELETE
        elif "bulk_delete" in request.POST:
            ids = request.POST.getlist("gallery_ids")
            Gallery.objects.filter(id__in=ids).delete()

        return redirect("gallery_upload")

    gallery = Gallery.objects.all().order_by("-id")
    images = Gallery.objects.filter(media_type="image").order_by("-id")
    videos = Gallery.objects.filter(media_type="video").order_by("-id")

    return render(request, "dashboard/gallery_upload.html", {
        "gallery": gallery,
        "images": images,
        "videos": videos
    })
    
def gallery_view(request):
    gallery = Gallery.objects.all().order_by('-created_at')
    
    return render(request, 'gallery_upload.html', {'gallery': gallery})

def image_view(request):

    gallery = Gallery.objects.all().order_by("-id")

    images = Gallery.objects.filter(media_type="image")
    videos = Gallery.objects.filter(media_type="video")

    total_galleries = gallery.count()
    total_images = images.count()

    categories = Gallery.objects.values_list('category', flat=True).distinct()

    context = {
        'gallery': gallery,
        'images': images,
        'videos': videos,
        'total_galleries': total_galleries,
        'total_images': total_images,
        'categories': categories,
    }

    return render(request, 'image_view.html', context)

    
@login_required
def download_note(request, note_id):
    note = get_object_or_404(ClassNote, id=note_id, uploaded_by=request.user)
    file_path = os.path.join(settings.MEDIA_ROOT, note.file.name)
    
    if os.path.exists(file_path):
        return FileResponse(
            open(file_path, 'rb'),
            content_type='application/octet-stream',
            as_attachment=True,
            filename=note.file.name.split('/')[-1]
        )
    else:
        messages.error(request, 'File not found.')
        return redirect('upload_notes')
    
#================ Certificate function =================== 

def certification_management(request):
    # Stats calculation
    total = Certificate.objects.count()
    issued = Certificate.objects.filter(status='issued').count()
    verified = Certificate.objects.filter(status='verified').count()
    pending = Certificate.objects.filter(status='pending').count()
    expired = Certificate.objects.filter(
        status='issued', 
        expiry_date__lt=timezone.now().date()
    ).count()
    
    # Search and filter
    query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "all")
    
    certificates = Certificate.objects.all()
    
    if query:
        certificates = certificates.filter(
            Q(student_name__icontains=query) |
            Q(certified_course__icontains=query) |
            Q(stu_id__icontains=query) |
            Q(cert_id__icontains=query)
        )
    
    if status_filter != 'all':
        certificates = certificates.filter(status=status_filter)
    
    context = {
        'total_certificates': Certificate.objects.count(),
        'issued_certificates': Certificate.objects.filter(status='issued').count(),
        'verified_certificates': Certificate.objects.filter(status='verified').count(),
        'pending_certificates': pending,  # <-- Pending count
        'expired_certificates': Certificate.objects.filter(
            status='issued',
            expiry_date__lt=timezone.now().date()
        ).count(),
        'certificates': certificates[:10],
}
    return render(request, 'dashboard/certification_management.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def upload_certificate(request):
    try:
        # Direct POST/FILES extraction
        stu_id = request.POST.get('stu_id', '').strip().upper()
        student_name = request.POST.get('student_name', '').strip()
        certified_course = request.POST.get('certified_course', '').strip()
        batch = request.POST.get('batch', '').strip()
        issued_date_str = request.POST.get('issued_date', '')
        certificate_file = request.FILES.get('certificate_file')
        
        # Validation
        if not all([stu_id, student_name, certified_course, batch, issued_date_str, certificate_file]):
            return JsonResponse({
                'success': False,
                'error': 'All fields are required!'
            }, status=400)
        
        # Check duplicate stu_id
        if Certificate.objects.filter(stu_id=stu_id).exists():
            return JsonResponse({
                'success': False,
                'error': f'Certificate for Student ID {stu_id} already exists!'
            }, status=400)
        
        # File size check (5MB)
        if certificate_file.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File size must be less than 5MB!'
            }, status=400)
        
        # Parse date
       
        issued_date = datetime.strptime(issued_date_str, '%Y-%m-%d').date()
        
        # Create certificate
        certificate = Certificate.objects.create(
            stu_id=stu_id,
            student_name=student_name,
            certified_course=certified_course,
            batch=batch,
            issued_date=issued_date,
            certificate_file=certificate_file
        )
        total = Certificate.objects.count()
        
        return JsonResponse({
            'success': True,
            'message': 'Certificate uploaded successfully!',
            'cert_id': certificate.cert_id,
            'stu_id': certificate.stu_id,
            'total_certificates': total,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)

def verify_certificate(request, cert_id):
    certificate = get_object_or_404(Certificate, cert_id=cert_id)

    if certificate.status == 'pending':
        certificate.status = 'issued'
        certificate.verified_at = timezone.now()
        certificate.save()

    messages.success(request, f'Certificate {cert_id} verified!')

    return redirect('certification_management')

def download_certificate(request, cert_id):
    certificate = Certificate.objects.get(cert_id=cert_id)
    response = FileResponse(
        certificate.certificate_file.open(),
        as_attachment=True,
        filename=f"{certificate.cert_id}.pdf"
    )
    return response

# Bulk export CSV
def export_csv(request):
  
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="certificates.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Cert ID', 'Student ID', 'Name', 'Course', 'Batch', 'Issued', 'Status'])
    
    certificates = Certificate.objects.all()
    for cert in certificates:
        writer.writerow([
            cert.cert_id,
            cert.stu_id,
            cert.student_name,
            cert.certified_course,
            cert.batch,
            cert.issued_date,
            cert.status
        ])
        
    
    return response   

@require_POST
def bulk_update_certificates(request):
    try:
        data = json.loads(request.body)
        cert_ids = data.get('cert_ids', [])
        action = data.get('action', '').lower()

        if not cert_ids or not action:
            return JsonResponse({'success': False, 'error': 'Invalid request'})

        updated_count = Certificate.objects.filter(cert_id__in=cert_ids).update(status=action)

        return JsonResponse({
            'success': True,
            'message': f'{updated_count} certificate(s) updated to {action.upper()}'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
# views.py


#================== Upload photo ====================
@require_http_methods(["POST"])
def upload_profile_photo(request):
    try:
        stu_id = request.POST.get('stu_id')
        profile_image = request.FILES.get('profile_image')
        
        if not stu_id or not profile_image:
            return JsonResponse({'success': False, 'error': 'Student ID and image required'}, status=400)
        
        student = admission.objects.get(id=stu_id)
        
        # Validate image
        if profile_image.size > 2 * 1024 * 1024:  # 2MB
            return JsonResponse({'success': False, 'error': 'Image too large (max 2MB)'}, status=400)
        
        # Resize image (optional)
        img = Image.open(profile_image)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail((300, 300))  # Max 300x300
        
        # Save
        profile_image.seek(0)  # Reset file pointer
        student.profile_image = profile_image
        student.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile photo updated!',
            'image_url': student.profile_image.url
        })
        
    except admission.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
