# microservice-auth
A microservice that provides authentication / authorization features for Open Matchmaking platform.

The project is focused on the building a blazingly fast and scalable authentication / authorization layer for Open Matchmaking microservices. It provides an information about users and allows to use JSON Web Tokens, so that it all of those data can be used for communicating with other microservices.

## Using
- [Sanic framework](https://sanic.readthedocs.io/en/latest/) 
- [Redis](https://redis.io/) with [aioredis](http://aioredis.readthedocs.io/en/v1.1.0/) library
- [MongoDB]() with [motor](https://motor.readthedocs.io/) library

## Documentation
An Information about when and how can be used you can find [here](https://github.com/OpenMatchmaking/documentation/blob/master/docs/architecture.md#with-authauth-microservice).
The general documentation about this microservice and available API is located [here](https://github.com/OpenMatchmaking/documentation/blob/master/docs/components/auth-microservice.md).
