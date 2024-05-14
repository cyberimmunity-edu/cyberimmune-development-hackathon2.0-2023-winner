SHELL := bash

MODULES := monitor \
           communication \
		   chipher \
		   data-analyze \
		   autopilot \
		   manager \
		   send-atm \
		   ins \
		   gnss \
		   nav \
		   def-storage \
		   data-gruber \
		   battery-critical \
		   battery \
		   emergency \
		   emergency-servos \
		   health-check \
		   servos \
		   drone-data \
		   processing \
		   storage

SLEEP_TIME := 20

all:
	docker-compose up --build -d
	sleep ${SLEEP_TIME}

	for MODULE in ${MODULES}; do \
		echo Creating $${MODULE} topic; \
		docker exec broker \
			kafka-topics --create --if-not-exists \
			--topic $${MODULE} \
			--bootstrap-server localhost:9092 \
			--replication-factor 1 \
			--partitions 1; \
	done

clean:
	docker-compose down

logs:
	docker-compose logs -f --tail 100

test:
	python3 simple-test.py