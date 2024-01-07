let ratingsData = [];

// Function to add rating - Call this when a user selects a rating
function addRating(user_id, movie_id, score) {
    let rating = {
        user_id: user_id,
        movie_id: movie_id,
        score: score
    };
    ratingsData.push(rating);
    // Optionally store in localStorage/sessionStorage
}

// Function to send data to the server
function sendRatingsToServer() {
    // Use AJAX to send data
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/submit_ratings", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify({ratings: ratingsData}));
}

// Trigger when user leaves the page
window.onbeforeunload = function() {
    sendRatingsToServer();
    return null;
};