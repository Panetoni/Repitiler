# Running the Django server
run-django:
	python3 Repitiler/manage.py runserver

run-django-in-0_0_0_0:
	python Repitiler/manage.py runserver 0.0.0.0:8000

# Run migrations: makemigrations + migrate
migrate:
	python3 Repitiler/manage.py makemigrations
	python3 Repitiler/manage.py migrate

# Create Django superuser (admin)
superuser:
	python3 Repitiler/manage.py createsuperuser

reload:
	touch Repitiler/manage.py