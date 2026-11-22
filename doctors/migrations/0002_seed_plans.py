from django.db import migrations

PLANS = [
    ("Basic", 0, 30, 10, 1, False,
     "Listed in doctor search\nUp to 10 appointments / month\nBasic clinic profile"),
    ("Standard", 499, 30, 100, 2, True,
     "Everything in Basic\nUp to 100 appointments / month\nPriority listing in your city\nEmail support"),
    ("Premium", 999, 30, 1000, 3, False,
     "Everything in Standard\nUnlimited appointments\nTop placement in search\nUp to 3 specializations\nPriority support"),
]


def seed(apps, schema_editor):
    Plan = apps.get_model("doctors", "SubscriptionPlan")
    for name, price, days, max_appts, max_specs, featured, features in PLANS:
        Plan.objects.get_or_create(plan_name=name, defaults=dict(
            price=price, duration_days=days, max_appointments=max_appts,
            max_specializations=max_specs, is_featured=featured, features=features,
        ))


def unseed(apps, schema_editor):
    apps.get_model("doctors", "SubscriptionPlan").objects.filter(plan_name__in=[p[0] for p in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("doctors", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
