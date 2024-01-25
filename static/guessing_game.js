// Function to add rating - Call this when a user selects a rating
function guess(movie_id, correct_guess) {
    
    if (movie_id == correct_guess) {
        alert("Correct guess! You win!");
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
    else {
        alert("Incorrect guess. Try again!");
    }
    
}