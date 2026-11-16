# Vehicle Service Management System (VSMS)

A full-stack Vehicle Service Management System built with **Python 3.14**, **Django 5.1**, **MySQL 8.0**, and **Bootstrap 5**.

---

## 🌟 Core Requirement Highlight

> **Independent Mechanic Selection**: Customers browse verified mechanics, compare experience, labour rates, and customer reviews, and independently book their preferred mechanic. The administrator manages and audits the platform, but **does not assign mechanics**.

---

## 🏗️ Architecture & Modules

### 1. Customer Module

- **Registration & Authentication**: Sign up as a vehicle owner.
- **Vehicle Garage (CRUD)**: Add, edit, and delete bikes and cars with registration plates and fuel types.
- **Browse & Filter Mechanics**: Search mechanics by name, skill, workshop name, city, and availability.
- **Mechanic Direct Selection**: View detailed profile, hourly rate, customer reviews, and specialized services.
- **Book Service**: Choose vehicle, preferred mechanic, service type, appointment date, and time slot.
- **Live Status Tracking**: Watch job status move from *Pending* &rarr; *Accepted* &rarr; *Vehicle Received* &rarr; *In Progress* &rarr; *Completed*.
- **Invoice & Online Settlement**: View transparent tax invoice with itemized spare parts, labour, and 18% GST. Simulate instant payment.
- **Rate & Review**: Submit 1 to 5 star ratings and reviews for completed services.

### 2. Mechanic Module

- **Registration**: Register workshop/independent profile with experience, specializations, hourly rate, and location.
- **Admin Verification Gate**: Account remains in *Pending Approval* until verified by Admin.
- **Availability Toggle**: 1-click toggle between *Available for Bookings* and *Busy*.
- **Booking Requests Queue**: Review incoming appointment requests and Accept or Reject with reason.
- **Active Repair Jobs**: Update vehicle status as repairs progress.
- **Service Completion & Invoicing**: Enter labour fee, spare parts used, and technical notes; generates final invoice.
- **Custom Service Rates**: Define custom prices for catalog services.
- **Earnings & Reviews**: Track completed jobs, total revenue, and customer feedback.

### 3. Admin Module

- **Platform Analytics**: Total customers, verified mechanics, active bookings, and platform revenue.
- **Mechanic Verification Queue**: 1-click *Approve* or *Reject* new mechanic applications.
- **Catalog Management**: Add, update, and manage vehicle services, estimated hours, base prices, and icons.
- **Platform Bookings Monitor**: Audit all appointments across the system.
- **Payments Monitor**: View transaction logs and financial records.

---

## 🗄️ Database Schema (MySQL)

- `auth_user`: Django authentication credentials.
- `accounts_customerprofile`: Phone, address, city, linked to User.
- `accounts_mechanicprofile`: Experience, specialization, workshop name, hourly rate, availability, approval status (`PENDING`, `APPROVED`, `REJECTED`).
- `customers_vehicle`: Vehicle type (2-Wheeler / 4-Wheeler), name, registration plate, year, fuel type.
- `services_service`: Standard services catalog, base price, estimated hours, category, icon.
- `mechanics_mechanicservice`: Custom rates and turnaround times set by individual mechanics.
- `bookings_booking`: Unique booking number, customer, vehicle, mechanic, service, schedule, and live status.
- `billing_invoice`: Unique invoice number, labour charge, spare parts breakdown, 18% GST, and grand total.
- `billing_payment`: Transaction ID, payment method (UPI / Card / NetBanking / Cash), payment status.
- `billing_review`: Customer rating (1-5 stars) and review text.

---

## 🚀 Quick Start Guide

### 1. Activate Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Verify Database Connection & Migrations

```powershell
python manage.py check
python manage.py migrate
```

### 3. Run Development Server

```powershell
python manage.py runserver
```http://127.0.0.1:8000
Open **[](http://127.0.0.1:8000)** in your web browser.

---

## 🔑 Local Admin Account

Create your own administrator after configuring the database:

```powershell
python manage.py createsuperuser
```

Do not use shared demo credentials. Store secrets in an untracked .env file.

---

## ⚙️ Environment Setup

Copy `.env.example` to `.env`, then edit `.env` and set the MySQL password you use locally. The settings loader reads `.env` automatically, and `.env` is ignored by Git.

Create the database once in MySQL Workbench if it does not already exist:

```sql
CREATE DATABASE vehicle_service_db CHARACTER SET utf8mb4;
```

Then run migrations:

```powershell
python manage.py migrate
```


---

## 🧪 Automated Test Suite
Run the full automated test suite verifying all 7 core business rules and workflows:
```powershell
python vehicle_service/test_system.py
```
