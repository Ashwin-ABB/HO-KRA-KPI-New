app_name = "kra_kpi"
app_title = "KRA KPI"
app_publisher = "Pupa"
app_description = "Employee KRA / KPI master and monthly score entry"
app_email = "admin@example.com"
app_license = "mit"
required_apps = ["frappe", "hrms"]

after_install = "kra_kpi.install.ensure_defaults"
after_migrate = ["kra_kpi.install.ensure_defaults"]
