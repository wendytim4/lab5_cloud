from flask import Flask, jsonify, request
from google.cloud import firestore

# Initialize Flask app
app = Flask(__name__)


db = firestore.Client()



# 1. Registering a student as a voter
@app.route('/voters', methods=['POST'])
def register_voter():
    voter_data = request.get_json()
    voter_id = voter_data['voter_id']
    name = voter_data['name']
    year_group = voter_data['year_group']
    major = voter_data['major']
    # Check if voter already exists
    voter_ref = db.collection('voters').document(voter_id)
    if voter_ref.get().exists:
        return jsonify({'message': 'Voter already registered'}), 400
    # Add voter to Firestore
    voter_ref.set({
        'name': name,
        'year_group': year_group,
        'major': major
    })
    return jsonify({'message': 'Voter registered successfully'}), 200



# 2. De-registering a student as a voter
@app.route('/voters/<voter_id>', methods=['DELETE'])
def deregister_voter(voter_id):
    # Check if voter exists
    voter_ref = db.collection('voters').document(voter_id)
    if not voter_ref.get().exists:
        return jsonify({'message': 'Voter not found'}), 404
    # Delete voter from Firestore
    voter_ref.delete()
    return jsonify({'message': 'Voter de-registered successfully'}), 200



# 3. Updating a registered voter's information
@app.route('/voters/<voter_id>', methods=['PUT'])
def update_voter(voter_id):
    voter_data = request.get_json()
    # Check if voter exists
    voter_ref = db.collection('voters').document(voter_id)
    if not voter_ref.get().exists:
        return jsonify({'message': 'Voter not found'}), 404
    # Update voter information in Firestore
    voter_ref.update(voter_data)
    return jsonify({'message': 'Voter information updated successfully'}), 200



# 4. Retrieving a registered voter
@app.route('/voters/<voter_id>', methods=['GET'])
def get_voter(voter_id):
    # Check if voter exists
    voter_ref = db.collection('voters').document(voter_id)
    if not voter_ref.get().exists:
        return jsonify({'message': 'Voter not found'}), 404
    # Get voter information from Firestore
    voter = voter_ref.get().to_dict()
    voter['voter_id'] = voter_id
    return jsonify(voter), 200



# 5. Creating an election
@app.route('/elections', methods=['POST'])
def create_election():
    election_data = request.get_json()
    election_name = election_data['election_name']
    # Add election to Firestore
    election_ref = db.collection('elections').document()
    election_ref.set({
        'election_name': election_name,

    })
    election_id = election_ref.id
    return jsonify({'message': 'Election created successfully', 'election_id': election_id}), 200


# Add candidates to an election
@app.route('/elections/<election_id>/candidates', methods=['POST'])
def add_candidate(election_id):
    # Check if election exists
    election_ref = db.collection('elections').document(election_id)
    if not election_ref.get().exists:
        return jsonify({'message': 'Election not found'}), 404
    
    # Get candidate data from request body
    candidate_data = request.get_json()
    # Add candidate to Firestore
    candidates_ref = election_ref.collection('candidates')
    candidate_ref = candidates_ref.add(candidate_data)
    candidate_id = candidate_ref[1].id
    # Return candidate ID
    return jsonify({'id': candidate_id}), 201



# 6. Retrieving an election (with its details)
@app.route('/elections/<election_id>', methods=['GET'])
def get_election(election_id):
    # Check if election exists
    election_ref = db.collection('elections').document(election_id)
    if not election_ref.get().exists:
        return jsonify({'message': 'Election not found'}), 404
    # Get election details from Firestore
    election_data = election_ref.get().to_dict()
    # Get candidate details from Firestore
    candidates_data = []
    candidates_ref = election_ref.collection('candidates')
    for candidate in candidates_ref.stream():
        candidate_data = candidate.to_dict()
        candidate_data['id'] = candidate.id
        candidates_data.append(candidate_data)
    # Get vote details from Firestore
    votes_data = []
    votes_ref = election_ref.collection('votes')
    for vote in votes_ref.stream():
        vote_data = vote.to_dict()
        vote_data['id'] = vote.id
        votes_data.append(vote_data)
    # Add candidates and votes data to election data
    election_data['candidates'] = candidates_data
    election_data['votes'] = votes_data
    return jsonify(election_data), 200




    
# 7. Deleting an election
@app.route('/elections/<election_id>', methods=['DELETE'])
def delete_election(election_id):
    # Check if election exists
    election_ref = db.collection('elections').document(election_id)
    if not election_ref.get().exists:
        return jsonify({'message': 'Election not found'}), 404
    # Delete election from Firestore
    election_ref.delete()
    return jsonify({'message': 'Election deleted successfully'}), 200

# 8. Voting in an election
@app.route('/elections/<election_id>/vote', methods=['POST'])
def vote(election_id):
    vote_data = request.get_json()
    voter_id = vote_data['voter_id']
    candidate_id = vote_data['candidate_id']
    # Check if voter and candidate exist
    voter_ref = db.collection('voters').document(voter_id)
    candidate_ref = db.collection('elections').document(election_id).collection('candidates').document(candidate_id)
    if not voter_ref.get().exists:
        return jsonify({'message': 'Voter not found'}), 404
    if not candidate_ref.get().exists:
        return jsonify({'message': 'Candidate not found'}), 404
    # Check if voter has already voted in the election
    election_ref = db.collection('elections').document(election_id)
    if voter_id in election_ref.get().to_dict().get('voters_voted', []):
        return jsonify({'message': 'Voter has already voted in this election'}), 400
    # Add vote to Firestore
    vote_ref = election_ref.collection('votes').document()
    vote_ref.set({
        'voter_id': voter_id,
        'candidate_id': candidate_id
    })
    # Update election's voters_voted field
    election_ref.update({
        'voters_voted': firestore.ArrayUnion([voter_id])
    })
    return jsonify({'message': 'Vote recorded successfully'}), 200


