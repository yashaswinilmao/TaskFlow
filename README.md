# TaskFlow — To-Do Application + CI/CD

A responsive Flask to-do app with user accounts, task CRUD, priorities, due dates, search/filter, Docker packaging, Jenkins pipeline, and Kubernetes manifests.

## 1. Features

- Register and log in with securely hashed passwords
- Create, edit, complete, and delete tasks
- Set Low / Medium / High priority and optional due dates
- Search tasks and filter All / Active / Completed
- Each user can only access their own tasks
- SQLite database persisted in a Docker volume / Kubernetes PVC
- Dockerfile, Docker Compose, Jenkinsfile, Kubernetes Deployment + Service + PVC
- Pytest test suite

## 2. Run locally on Windows

Open PowerShell in the project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**.

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

To stop Flask, press `Ctrl+C` in the terminal.

## 3. Run tests

```powershell
python -m pytest -v
```

## 4. Run with Docker

Make sure Docker Desktop is running:

```powershell
docker build -t taskflow:latest .
docker run --name taskflow -p 5000:5000 -e SECRET_KEY="change-this-secret" -v taskflow_data:/app/instance taskflow:latest
```

Open http://localhost:5000. To stop/remove:

```powershell
docker stop taskflow
docker rm taskflow
```

Or use Docker Compose:

```powershell
docker compose up --build -d
docker compose logs -f
docker compose down
```

## 5. Push image to Docker Hub

1. Create a Docker Hub repository named `taskflow`.
2. Sign in: `docker login`.
3. Replace `DOCKERHUB_USERNAME` in `Jenkinsfile` and `k8s/deployment.yaml` with your Docker Hub username.
4. Build, tag and push manually if needed:

```powershell
docker build -t YOUR_DOCKERHUB_USERNAME/taskflow:latest .
docker push YOUR_DOCKERHUB_USERNAME/taskflow:latest
```

## 6. Kubernetes deployment

Requirements: a working Kubernetes cluster (Docker Desktop Kubernetes, Minikube, or another cluster), and `kubectl` configured to use it.

1. Replace `DOCKERHUB_USERNAME` in `k8s/deployment.yaml`.
2. Create the app secret (edit the sample value first):

```powershell
kubectl apply -f k8s/secret.example.yaml
```

For a real project, copy the example to `secret.yaml`, use a strong random secret, and do not commit that file.
3. Apply the resources:

```powershell
kubectl apply -f k8s/deployment.yaml
kubectl get pods
kubectl get services
```

4. Open **http://localhost:30080** when using Docker Desktop Kubernetes. With Minikube, run:

```powershell
minikube service taskflow
```

Check logs:

```powershell
kubectl logs deployment/taskflow
```

## 7. Jenkins CI/CD setup (Windows Jenkins agent)

The included Jenkinsfile is written for a Windows agent because it uses `bat` commands. The agent needs Python, Docker CLI/Desktop, Git, and (for deployment) kubectl installed and available on PATH.

1. Put this project in a Git repository and push it to GitHub.
2. Create a Jenkins Pipeline job and configure it to use the repository's `Jenkinsfile`.
3. Add Jenkins username/password credential for Docker Hub. Set the credential ID in a Jenkins environment variable named `DOCKERHUB_CREDENTIALS_ID`.
4. Add a Jenkins Secret file credential containing your kubeconfig. Set its ID as `KUBECONFIG_CREDENTIALS_ID`.
5. Replace `DOCKERHUB_USERNAME` in the Jenkinsfile with your Docker Hub username.
6. Configure a GitHub webhook to trigger the Jenkins job on pushes, or enable SCM polling in Jenkins.

Pipeline stages: Checkout → Install & Test → Build Docker Image → Push Docker Image → Deploy to Kubernetes.

If you use a Linux Jenkins agent, change `bat` steps to `sh` and use a Linux-compatible agent.

## 8. Suggested demonstration checklist

- Register two accounts and verify their task lists are private.
- Add tasks with different priorities and due dates.
- Complete, edit, delete, search, and filter tasks.
- Run `pytest` and show passing tests.
- Build and run the Docker container.
- Show Jenkins pipeline stages succeeding.
- Show Kubernetes pods and service with `kubectl get pods,svc`.

## Notes

- The Flask development server is for local development only. Docker runs Gunicorn.
- Change the default `SECRET_KEY` before sharing or deploying.
- SQLite with one replica is suitable for a college demonstration. For a production multi-replica deployment, use PostgreSQL and a managed persistent database.
- The Kubernetes PVC storage behavior depends on your cluster's storage provisioner.
