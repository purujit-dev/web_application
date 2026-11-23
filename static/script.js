// Live search filter for Books on index.html
var bookSearchInput = document.getElementById("bookSearch");
if (bookSearchInput) {
    bookSearchInput.addEventListener("keyup", function () {
        var query = bookSearchInput.value.toLowerCase().trim();
        var cards = document.querySelectorAll(".book-card");
        cards.forEach(function (card) {
            var text = card.getAttribute("data-search");
            if (text.indexOf(query) !== -1) {
                card.style.display = "block";
            } else {
                card.style.display = "none";
            }
        });
    });
}

// Live search filter for Customer Profiles on admin_profiles.html
var customerSearchInput = document.getElementById("customerSearch");
if (customerSearchInput) {
    customerSearchInput.addEventListener("keyup", function () {
        var query = customerSearchInput.value.toLowerCase().trim();
        var rows = document.querySelectorAll("#customerTable tbody tr");
        rows.forEach(function (row) {
            var text = row.getAttribute("data-search");
            if (text.indexOf(query) !== -1) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    });
}

// Simple confirmation dialog for delete actions
function confirmAction(message) {
    return confirm(message);
}

// Basic client-side form validation
function validateLoginForm() {
    var email = document.getElementById("email").value.trim();
    var password = document.getElementById("password").value;
    if (email === "" || password === "") {
        alert("Please fill in both email and password.");
        return false;
    }
    return true;
}

function validateRegisterForm() {
    var name = document.getElementById("name").value.trim();
    var password = document.getElementById("password").value;
    if (name.length < 2) {
        alert("Please enter your full name.");
        return false;
    }
    if (password.length < 6) {
        alert("Password must be at least 6 characters long.");
        return false;
    }
    return true;
}
