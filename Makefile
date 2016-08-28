all: bootstrap less static test

bower_components/bootstrap/dist/css/bootstrap.css: bower_components/bootstrap/package.json less/bs-achieve-variables.less
	cd bower_components/bootstrap && grunt dist

achieve/static/css/achieve.css: less/achieve.less less/bs-achieve-variables.less less/navigation-main.less less/signin.less less/snackbar.less less/tables.less less/task-page.less
	lessc less/achieve.less > achieve/static/css/achieve.css

bootstrap: bower_components/bootstrap/dist/css/bootstrap.css

less: achieve/static/css/achieve.css

static: bootstrap less
	./manage.py collectstatic --noinput

test:
	DJANGO_SETTINGS_MODULE=achieveapp.settings py.test
	coverage html
