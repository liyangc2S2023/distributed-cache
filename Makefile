test:
	python3 tests/test_final.py

test_local:
	python3 tests/test_final.py --kill_ports=True

build:
	pip3 install -r requirements.txt

doc:
	make -C docs clean html && make -C docs html