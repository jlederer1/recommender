// Function to add rating - Call this when a user selects a rating
function addRating(user_id, movie_id, score, elem_id) {
    let rating = {
        user_id: user_id,
        movie_id: movie_id,
        score: score
    };

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/submit_ratings", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify({ratings: [rating] }));

    //document.getElementById('element_${score}').classList.add('checked');
    console.log(elem_id);
    for (let i = 1; i <= 5; i++) {
        if (i <= score) {
            document.getElementById(`${movie_id}_${i}`).classList.add('checked');
          }
        else {
            document.getElementById(`${movie_id}_${i}`).classList.remove('checked');
        }
      }
}