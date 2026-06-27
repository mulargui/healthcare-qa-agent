"""Shared mock data for tests and evals."""

MOCK_DOCTORS = [
    {"Name": "Dr. Sarah Johnson, MD", "Address": "1234 Medical Ave", "City": "Seattle", "Classification": "Neurology"},
    {"Name": "Dr. Michael Chen, MD", "Address": "5678 Vision Blvd", "City": "Seattle", "Classification": "Ophthalmology"},
    {"Name": "Tana Anderson, MA, LMHC", "Address": "15600 Redmond Ave, Suite 101", "City": "Redmond", "Classification": "Counselor"},
    {"Name": "Dr. Robert Kim, MD", "Address": "300 Bone St", "City": "Redmond", "Classification": "Orthopedist"},
    {"Name": "Dr. Lisa Martinez, MD", "Address": "400 Heart Rd", "City": "Seattle", "Classification": "Cardiology"},
    {"Name": "Dr. David Brown, MD", "Address": "500 Cardiac Ave", "City": "Tacoma", "Classification": "Cardiology"},
]

MOCK_SEARCH_RESULTS = [
    {
        "title": "Common Cold vs Flu - Health Guide",
        "url": "https://example.com/cold-vs-flu",
        "content": "The common cold and flu are both respiratory illnesses caused by different viruses. "
                   "Flu symptoms are more severe: high fever, body aches, fatigue. Cold symptoms are milder: "
                   "runny nose, sneezing, sore throat.",
    },
    {
        "title": "Headache and Dizziness Causes",
        "url": "https://example.com/headache-dizziness",
        "content": "Recurring headaches combined with dizziness may indicate neurological conditions. "
                   "Common causes include migraines, vestibular disorders, or hypertension.",
    },
]
