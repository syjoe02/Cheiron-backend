import os

import pytest

# Set required env vars before any app modules are imported (they call Settings() at load time)
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")


@pytest.fixture
def sample_study() -> dict:
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678",
                "briefTitle": "Test Study: Aspirin in Heart Disease — Phase 2 Randomized Trial",
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"date": "2020-03-15"},
            },
            "designModule": {
                "phases": ["PHASE2"],
                "enrollmentInfo": {"count": 100},
            },
            "conditionsModule": {"conditions": ["Heart Disease", "Hypertension"]},
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Test University", "class": "OTHER"}
            },
            "armsInterventionsModule": {
                "interventions": [{"name": "Aspirin", "type": "DRUG"}]
            },
            "contactsLocationsModule": {
                "locations": [{"country": "United States"}]
            },
        }
    }


@pytest.fixture
def sample_study_phase3() -> dict:
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT87654321",
                "briefTitle": "Phase 3 Randomized Study: Pembrolizumab in Lung Cancer",
            },
            "statusModule": {
                "overallStatus": "COMPLETED",
                "startDateStruct": {"date": "2018-06"},
            },
            "designModule": {
                "phases": ["PHASE3"],
                "enrollmentInfo": {"count": 450},
            },
            "conditionsModule": {"conditions": ["Lung Cancer", "NSCLC"]},
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Merck Sharp & Dohme", "class": "INDUSTRY"}
            },
            "armsInterventionsModule": {
                "interventions": [{"name": "Pembrolizumab", "type": "DRUG"}]
            },
            "contactsLocationsModule": {
                "locations": [
                    {"country": "United States"},
                    {"country": "Germany"},
                ]
            },
        }
    }


@pytest.fixture
def mock_ct_response(sample_study) -> dict:
    return {"studies": [sample_study] * 10, "totalCount": 10}
