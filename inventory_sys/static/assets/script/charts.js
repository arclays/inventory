// Sales Chart
const ctx1 = document.getElementById("salesChart").getContext("2d");
const salesChart = new Chart(ctx1, {
  type: "line",
  data: {
    labels: ["January", "February", "March", "April", "May", "June"],
    datasets: [
      {
        label: "Sales ($)",
        data: [3000, 4000, 3500, 5000, 4500, 6000],
        backgroundColor: "rgba(54, 162, 235, 0.2)",
        borderColor: "rgba(54, 162, 235, 1)",
        borderWidth: 1,
      },
    ],
  },
  options: {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});

// Product Categories Chart
const ctx2 = document.getElementById("categoriesChart").getContext("2d");
const categoriesChart = new Chart(ctx2, {
  type: "pie",
  data: {
    labels: ["Electronics", "Furniture", "Clothing", "Books"],
    datasets: [
      {
        data: [40, 20, 25, 15],
        backgroundColor: [
          "rgba(255, 99, 132, 0.2)",
          "rgba(54, 162, 235, 0.2)",
          "rgba(255, 206, 86, 0.2)",
          "rgba(75, 192, 192, 0.2)",
        ],
        borderColor: [
          "rgba(255, 99, 132, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 206, 86, 1)",
          "rgba(75, 192, 192, 1)",
        ],
        borderWidth: 1,
      },
    ],
  },
});
document.getElementById("confirmLogout").addEventListener("click", function () {
  alert("Logged out successfully.");
  // Redirect to login page or home page
  // window.location.href = 'login.html';
});

// Save profile functionality (simple example)
document.getElementById("saveProfile").addEventListener("click", function () {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  // Implement your logic to save the profile here
  alert("Profile updated successfully!");
  // Close the modal
  const modal = bootstrap.Modal.getInstance(
    document.getElementById("profileModal")
  );
  modal.hide();
});

document.querySelectorAll(".deleteBtn").forEach((button) => {
  button.addEventListener("click", function (e) {
    e.preventDefault();

    const deleteUrl = this.href;
    Swal.fire({
      title: "Are you sure?",
      text: "This action cannot be undone!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Yes, delete it!",
      cancelButtonText: "Cancel",
    }).then((result) => {
      if (result.isConfirmed) {
        // If confirmed, redirect to the delete URL
        window.location.href = deleteUrl;
      }
    });
  });
});
