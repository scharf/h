 The following instructions were made to install SQL backend under Debian Linux. Hopefully it'll be similar for other distributions too.
 
 Setting up the Database
	1.	Install postgresql (i.e. apt-get install postgresql postgresql-client )
	2. 	Switch to posgres user (by default only root can do it) : 
		su - postgres
	3.	Enter the default db:
		psql template1
	4.  	Create a user used by the backend: 
		CREATE USER hypo_backend WITH PASSWORD 'myPassword';
	5.	Created a database for the backend:
		CREATE DATABASE hypo_db;
	6.	Grant priviledges for the created user on the created db:
		GRANT ALL PRIVILEGES ON DATABASE hypo_db to hypo_backend;
	7.	Quit from psql:
		\\q
	8.	Test your user (assuming your db is installed to localhost):
		psql -h localhost -d hypo_db -U hypo_backend
		After  giving the password you should see the hypo_db => prompt

 Pulling out the annotator-store project.
	1. 	Clone the project:
		git clone https://github.com/gergely-ujvari/annotator-store.git
	2.	cd annotator-store/
	3.	Switch to the branch:
		git checkout 46-Move-to-Pure-SQL-backend 

 Pulling out the hypothesis project
	1.	Clone the project
		git clone https://github.com/gergely-ujvari/h.git
	2.  	cd h/
	3.	Switch to the branch
		git checkout 46-Move-to-Pure-SQL-backend 

 Configuring
	1.	Configure localenv and boostrap as usual.
	2.	Set pip to use the checkout out annotator-store version:
		pip install -e <Annotator-store repo location>
	3.	Edit the development.ini to enter the connect_string
		backend.url: postgresql+psycopg2://<user>:<password>@<dbhost:port>/<db>
		i.e.

		backend.url: postgresql+psycopg2://hypo_backend:myPassword@localhost/hypo_db
	
If all works well then starting the application does not require a running elasticsearch instance and it'll work just as the original backend. :)
	
