<?php
session_start();

// Check if user is logged in
if (!isset($_SESSION['token'])) {
    header('Location: login.php');
    exit;
}

// Call API to fetch user data
$ch = curl_init('http://localhost:8000/api/user');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Authorization: Bearer ' . $_SESSION['token']
]);
$response = curl_exec($ch);
curl_close($ch);

$userData = json_decode($response, true);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/3.10.2/mdb.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1>Welcome, <?= htmlspecialchars($userData['name']) ?></h1>
        <a href="projects.php" class="btn btn-success">View Projects</a>
        <a href="campaigns.php" class="btn btn-info">View Campaigns</a>
        <a href="logout.php" class="btn btn-danger">Logout</a>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/3.10.2/mdb.min.js"></script>
</body>
</html>
