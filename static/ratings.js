// Function to add rating - Call this when a user selects a rating
function addRating(user_id, movie_id, score) {
    let rating = {
        user_id: user_id,
        movie_id: movie_id,
        score: score
    };

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/submit_ratings", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify({ratings: [rating] }));

}