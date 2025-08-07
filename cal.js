function hi() {
    alert("hi!");
}

function toggleCinema(cinemaName) {
    for (node of document.getElementsByClassName(cinemaName)) {
        if (node.classList.contains("hidden")) {
            node.classList.remove("hidden");
        } else {
            node.classList.add("hidden");
        }
    }
}

function toggleMovie(title) {
    for (node of document.getElementsByTagName("li")) {
        if (node.textContent == title) {
            if (node.classList.contains("hidden")) {
                node.classList.remove("hidden");
            } else {
                node.classList.add("hidden");
            }
        }
    }
}
