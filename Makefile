# Running the Django server
run-django:
	python3 manage.py runserver

run-django-in-0_0_0_0:
	python manage.py runserver 0.0.0.0:8000

# Run migrations: makemigrations + migrate
migrate:
	python3 manage.py makemigrations
	python3 manage.py migrate

# Create Django superuser (admin)
superuser:
	python3 manage.py createsuperuser

reload:
	touch manage.py