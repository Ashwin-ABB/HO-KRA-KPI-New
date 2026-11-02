# KRA KPI

Frappe app with two DocTypes (module **KRA**):

- **KPI Master** - one per employee: KRA, Goal Name, Target, Weightage (total must be 100).
- **Monthly KPI Entry** - employee picks a date, enters Actual Values; total score is calculated from the weightages.

Requires Frappe and HRMS (Employee DocType).

    bench get-app https://github.com/<owner>/<repo>
    bench --site <site> install-app kra_kpi
