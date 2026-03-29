import pytest
import uuid
from django.urls import reverse
from rest_framework.test import APIClient
from src.forest_connectivity.models import PipelineRun

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def valid_payload():
    return {
        "state": "Jharkhand",
        "district": "Ranchi",
        "block": "Kanke",
        "lulc_year": "2023_2024"
    }

@pytest.mark.django_db
def test_create_analysis_success(client, valid_payload, mocker):
    mocker.patch('src.forest_connectivity.tasks.compute_mspa_task.delay')
    
    response = client.post('/api/v1/forest-connectivity/', valid_payload, format='json')
    assert response.status_code == 202
    assert "task_id" in response.data
    assert response.data["status"] == "queued"

@pytest.mark.django_db
def test_create_analysis_invalid(client):
    response = client.post('/api/v1/forest-connectivity/', {}, format='json')
    assert response.status_code == 400

@pytest.mark.django_db
def test_idempotency(client, valid_payload, mocker):
    # Create an already completed run
    PipelineRun.objects.create(state='done', parameters=valid_payload)
    
    mocker.patch('src.forest_connectivity.tasks.compute_mspa_task.delay')
    response = client.post('/api/v1/forest-connectivity/', valid_payload, format='json')
    
    assert response.status_code == 200 # Should return 200 OK, not 202 ACCEPTED
    assert response.data["status"] == "completed"

@pytest.mark.django_db
def test_get_status(client):
    run = PipelineRun.objects.create(state='pending', parameters={})
    
    response = client.get(f'/api/v1/forest-connectivity/{run.id}/')
    assert response.status_code == 200
    assert response.data["status"] == "pending"
