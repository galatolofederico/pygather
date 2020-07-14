# pygather

Python script to track visitor IP and browser information and redirect him.

It supports:

* Custom redirect links
* Javascript information gathering
* Pure HTTP redirect

## Screenshots

| ![](README.md.d/admin.png) | ![](README.md.d/view.png) |
| --- | --- |

## Usage

The admin panel is accessible at `http(s)://<your-url>:<your-port>/admin`


## Deploy

### Docker

```
docker-compose up
```

`pygather` will be available at `http://<your-ip>:8080`

### Heroku

Make sure you have installed Heroku CLI, logged in and created a new project

Add heroku remote

```
heroku git:remote -a <project>
```

Push

```
git push origin heroku
```