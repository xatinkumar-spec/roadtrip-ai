from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import CustomSignupForm

def home(request):
    return render(request, "home.html")

def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)

        if form.is_valid():
            user = form.save()

            subject = "Welcome to RoadTrip AI"
            message = f"""
Hi {user.username},

Welcome to RoadTrip AI!

Your account has been successfully created.

Now you can:
- Plan your road trips
- Save destinations
- Explore travel ideas

If you ever forget your password, you can reset it using the Forgot Password option.

Happy travelling!

RoadTrip AI Team
"""

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print("Welcome email failed:", e)

            login(request, user)
            return redirect("home")

        else:
            print(form.errors)

    else:
        form = CustomSignupForm()

    return render(request, "signup.html", {"form": form})


def login_view(request):
    error_message = None

    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        if '@' in username_or_email:
            user_obj = User.objects.filter(email=username_or_email).first()
            if user_obj:
                username_or_email = user_obj.username
            else:
                error_message = "No account found with this email."

        user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        elif error_message is None:
            error_message = "Invalid username/email or password."

    return render(request, 'login.html', {'error_message': error_message})


def logout_view(request):
    logout(request)
    return redirect('home')