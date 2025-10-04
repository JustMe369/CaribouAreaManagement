# Caribou Area Management System

A comprehensive Django-based web application for managing Caribou Coffee store operations, maintenance, compliance tracking, and area management.

## 🚀 Features

### Core Functionality
- **Multi-Area Management** - Organize stores by geographical areas with user access control
- **Store Management** - Manage multiple Caribou Coffee locations with detailed information
- **Visit Tracking** - Record and track store visits with comprehensive checklists
- **Maintenance System** - Create, track, and manage maintenance tickets with priority levels
- **Compliance Monitoring** - Monitor compliance rates across all stores and areas
- **User Management** - Role-based access control with different permission levels
- **Reporting & Analytics** - Comprehensive dashboard with charts and export capabilities

### Dashboard Features
- Real-time KPI tracking (Total Visits, Compliance Rate, Monthly Statistics)
- Interactive charts for compliance trends and performance metrics
- Workload & maintenance status visualization
- Category and store performance analysis
- Recent visits and top-performing stores overview
- Action plan management and tracking

### Advanced Features
- **Draft System** - Save and resume incomplete checklists
- **File Attachments** - Upload photos and documents for visits and maintenance
- **Data Export** - Export to Excel, PDF, and CSV formats
- **Question Management** - Dynamic checklist question management
- **Action Plans** - Create and track follow-up actions with deadlines
- **Area-Based Access Control** - Users can only access assigned areas and stores

## 🛠️ Technology Stack

- **Backend**: Django 5.2.6
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Charts**: Chart.js for data visualization
- **Icons**: Font Awesome
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **File Processing**: OpenPyXL for Excel operations
- **Code Quality**: Ruff for linting

## 📁 Project Structure

```
CaribouAreaManagerControl/
├── caribou_dashboard/           # Django project configuration
│   ├── __init__.py
│   ├── asgi.py                 # ASGI configuration
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL routing
│   └── wsgi.py                 # WSGI configuration
├── checklist/                  # Main application
│   ├── management/             # Django management commands
│   │   └── commands/
│   ├── migrations/             # Database migrations
│   ├── templates/              # HTML templates
│   │   └── checklist/
│   │       ├── base.html       # Base template
│   │       ├── dashboard_*.html # Dashboard components
│   │       ├── maintenance_*.html # Maintenance templates
│   │       ├── store_*.html    # Store management templates
│   │       └── *.html          # Other feature templates
│   ├── templatetags/           # Custom template tags
│   │   └── checklist_tags.py
│   ├── utils/                  # Utility functions
│   │   ├── helpers.py
│   │   └── validators.py
│   ├── views/                  # Organized view modules
│   │   ├── __init__.py
│   │   ├── action_plan_views.py
│   │   ├── area_management_views.py
│   │   ├── base.py
│   │   ├── checklist_views.py
│   │   ├── dashboard_views.py
│   │   ├── data_export_views.py
│   │   ├── maintenance_views.py
│   │   ├── reports_views.py
│   │   └── store_views.py
│   ├── admin.py               # Django admin configuration
│   ├── apps.py                # App configuration
│   ├── forms.py               # Django forms
│   ├── models.py              # Database models
│   ├── tests.py               # Unit tests
│   └── urls.py                # App URL routing
├── users/                     # User management app
│   ├── migrations/            # User app migrations
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py              # User profile models
│   ├── signals.py             # Django signals
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/                 # Global templates
│   ├── admin/                 # Admin templates
│   ├── checklist/             # Checklist templates
│   ├── registration/          # Authentication templates
│   ├── users/                 # User management templates
│   └── baseD.html
├── static/                    # Static files (CSS, JS, images)
│   ├── admin/
│   │   ├── css/
│   │   └── js/
│   ├── checklist/
│   │   ├── css/
│   │   │   ├── dashboard.css
│   │   │   ├── history.css
│   │   │   ├── maintenance_list.css
│   │   │   └── new_checklist.css
│   │   └── js/
│   │       ├── area_management.js
│   │       ├── dashboard.js
│   │       ├── maintenance_list.js
│   │       ├── new_checklist.js
│   │       └── new_maintenance.js
│   └── users/
│       └── css/
├── staticfiles/               # Collected static files for production
├── media/                     # User uploaded files
│   ├── maintenance_attachments/
│   └── visit_attachments/
├── caribou_env/               # Virtual environment
├── .gitignore                 # Git ignore rules
├── .ruff_cache/               # Ruff linting cache
├── db.sqlite3                 # SQLite database
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/JustMe369/CaribouAreaManagement.git
cd CaribouAreaManagerControl
```

2. **Create virtual environment**
```bash
python -m venv caribou_env
# On Windows:
caribou_env\Scripts\activate
# On macOS/Linux:
source caribou_env/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Database setup**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Collect static files**
```bash
python manage.py collectstatic
```

7. **Run development server**
```bash
python manage.py runserver
```

8. **Access the application**
- Open browser and go to `http://127.0.0.1:8000`
- Login with superuser credentials

## 📊 Key Models

### Area
- Geographical area management
- User assignment to areas
- Store grouping by area

### Store
- Store information and location details
- Contact information and operational status
- Equipment categories and products
- Area assignment

### AreaManagerVisit
- Store visit records with comprehensive data
- Time tracking (in/out times)
- Overall scoring and grading system
- Draft functionality for incomplete visits

### ChecklistCategory & ChecklistQuestion
- Dynamic checklist management
- Categorized questions with numbering
- Active/inactive status control

### ChecklistItem
- Individual checklist responses
- Boolean answers with comments
- Follow-up requirement tracking

### MaintenanceTicket
- Maintenance request tracking
- Priority levels (Low, Medium, High)
- Status management (Pending, In Progress, Completed)
- File attachment support
- Due date tracking with overdue detection

### ActionPlanItem
- Follow-up action tracking
- Priority and status management
- Deadline monitoring

### User Profile System
- Role-based access control
- Area and store access permissions
- Multiple role types (Admin, Area Manager, Store Manager, etc.)

## 🎨 UI/UX Features

### Professional Design
- Clean, modern interface with Bootstrap 5
- Responsive design for all devices
- Professional color scheme and typography
- Intuitive navigation with role-based menus

### Dashboard Analytics
- Real-time statistics and KPIs
- Interactive Chart.js visualizations
- Performance trending and analysis
- Maintenance workload tracking
- Compliance rate monitoring

### Advanced Functionality
- Multi-criteria filtering system
- Real-time search capabilities
- Bulk operations for efficiency
- Export capabilities (Excel, PDF, CSV)
- Pagination for large datasets
- File upload and attachment system

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Dependencies
```
asgiref==3.9.1
claude==0.4.11
crispy-bootstrap5==2025.6
Django==5.2.6
django-crispy-forms==2.4
et_xmlfile==2.0.0
openpyxl==3.1.5
ruff==0.13.1
sqlparse==0.5.3
tzdata==2025.2
```

## 📈 Usage

### Area Management
1. Create geographical areas
2. Assign users to areas
3. Assign stores to areas
4. Monitor area performance

### Store Visit Management
1. Navigate to "New Visit" from dashboard
2. Select store location
3. Complete checklist items with comments
4. Add maintenance requests if needed
5. Create action plan items
6. Submit or save as draft

### Maintenance Management
1. Access "Maintenance" from navigation
2. Create tickets with priority levels
3. Track progress and update status
4. Attach files and photos
5. Monitor due dates and overdue items
6. Export reports as needed

### Analytics & Reporting
1. Dashboard provides real-time overview
2. Use filters to analyze specific periods
3. Export data for external reporting
4. Monitor compliance trends
5. Track action plan completion

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in settings
2. Configure production database (PostgreSQL recommended)
3. Set up static file serving with web server
4. Configure ALLOWED_HOSTS
5. Use WSGI server (gunicorn recommended)
6. Set up SSL/HTTPS
7. Configure media file serving

### Security Considerations
- Use strong SECRET_KEY in production
- Enable HTTPS
- Configure proper CORS settings
- Set up database security
- Regular security updates
- Implement proper backup strategy

## 🧪 Testing

Run tests with:
```bash
python manage.py test
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check documentation for common solutions

## 🔄 Version History

- **v1.0.0** - Initial release with core functionality
- **v1.1.0** - Enhanced dashboard and maintenance system
- **v1.2.0** - Professional UI upgrade and advanced filtering
- **v1.3.0** - Area management and user access control
- **v1.4.0** - File attachments and export capabilities

---

**Caribou Area Management System** - Streamlining coffee shop operations with modern technology and comprehensive management tools.
