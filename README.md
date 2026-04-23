*Note: This project focused on building an asynchronous data pipeline. The core architecture developed here has since evolved into a separate open-source blockchain data lakehouse called evm-iceberg.*

jars is a distributed stream-processing engine built to figure out how to handle high-frequency WebSocket data without dropping packets. To test the infra in a real world scenario, a standard SaaS business layer for cex copy-trading (handling user auth, routing, and balances) was built on top of it. The main goal of this project was to learn how to manage distributed task queues and prevent race conditions during concurrent state updates using Python, Redis, and Kafka.

### Run Locally

##### Prerequisites
* Docker & Docker Compose installed and running.
* Python 3.11+ (if executing local CLI commands).
* Git

##### 1. Clone and Configure
Pull the repository and set up your local environment variables.

```bash
git clone https://github.com/YOUR_USERNAME/jars.git
cd jars

# Create your local environment file
cp .env.example .env
```

##### 2. Boot the Infrastructure
Spin up the entire pipeline (Broker, Cache, Database, and Celery Workers) in the background.

```bash
docker compose up -d
```

##### 3. Verify System Health
Check that all containers have successfully started and are communicating.

```bash
docker compose ps
```
*(Note: If a service fails to boot, inspect it using docker compose logs <service_name>)*


##### 4. Teardown
When finished, spin down the cluster. The -v flag wipes the local database and message broker volumes so you start with a clean slate next time.

```bash
docker compose down -v
```
