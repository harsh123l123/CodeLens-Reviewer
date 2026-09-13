<?php
// Legacy e-commerce catalog search endpoint
// High-severity security issues: Hardcoded DB credentials, SQL Injection, Reflected XSS

$host = "localhost";
$user = "db_admin";
$pass = "SuperSecretDbPassword2026!";
$dbname = "ecommerce_production";

$conn = new mysqli($host, $user, $pass, $dbname);

if ($conn->connect_error) {
    die("Database Connection failed: " . $conn->connect_error);
}

// Unvalidated user query parameter
$search_keyword = $_GET['q'];
$sort_order = $_GET['sort'];

// CRITICAL SECURITY: Direct concatenation into SQL statement allows full DB extraction
$query = "SELECT id, title, price, description FROM products WHERE title LIKE '%" . $search_keyword . "%' ORDER BY " . $sort_order;
$result = $conn->query($query);

echo "<h1>Search Results for: " . $search_keyword . "</h1>"; // Reflected XSS

if ($result && $result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        echo "<div class='product-box'>";
        echo "<h3>" . $row["title"] . "</h3>";
        echo "<p>" . $row["description"] . "</p>";
        echo "<strong>$" . $row["price"] . "</strong>";
        echo "</div>";
    }
}
?>
