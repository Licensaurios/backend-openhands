deb:
	docker build -f Dockerfile --target builder -t sholsapp/server-builder .
	docker create --cidfile .tmp-docker-container-id sholsapp/server-builder
	xargs -I {} docker cp -a "{}:/build/server_0.1-1_amd64.deb" . < .tmp-docker-container-id
	xargs -I {} docker rm -f "{}" < .tmp-docker-container-id
	rm .tmp-docker-container-id

docker:
	docker build -t sholsapp/server:0.1 .
	docker run --cidfile .server-container-id --publish 8080:8080 --detach sholsapp/server:0.1

clean:
	git clean -fxd -e infra

