
# REST-API rate limiting with Cache (Redis)  

<div>
    <img height="70" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/redis/redis-original.svg" />
    <img height="70" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/fastapi/fastapi-original.svg">
</div>

<p>
 Rate limiting is a very important aspect in Rest-API to prevent Clients or Rogue users from overusing 
 an API endpoints (Preventing DOSs (denial of service attacks)). There are many great techniques for rate limiting. Here is a very simple implementation, That demos Rate limiting for particular users. So we have one endpoint which enables, users to get data from the External API on the weather. The limit is by default of 1 request per minute!
</p>


<details>
<summary>Project External Dependencies</summary>
<ul>
<li>Python framework FastAPI (version 0.0.6 CLI)</li>
<li>SQLmodel (SQL ORM) using sqlite3</li>
<li>Redis and Redis connector with python</li>
<li>passlib (Crypto library)</li>
<li>jose for JSON Web token handling!</li>
</ul>
</details>

<p>
 External API used: <a href="https://www.weatherapi.com/">Free Weather API</a>
</p>

<h4>Make sure to create a .env file with the variables: (SECRET_KEY, TOKEN_EXPIRE_TIME,HOST,ALGORITHM, WEATHER_API_KEY)</h4>

<h5>Run the server with</h5>

```
$: fastapi dev main.py
```
