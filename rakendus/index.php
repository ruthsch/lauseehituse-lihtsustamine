<?php
setlocale(LC_ALL, 'et_EE.UTF-8');

$sisend = "";
$tulemus = "";
if (isset($_POST['sisend'])) {
    $sisend = trim(htmlspecialchars($_POST['sisend']));
    $tulemus = shell_exec(escapeshellcmd('LC_ALL=et_EE.UTF-8 python3 lihtsustamine.py '."'".$sisend."'")." arg 2>&1");
}
?>

<html>
	<head>
		<link rel="stylesheet" href="static/css/site.css">
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<meta charset="utf-8">
		<title>Lauseehituse lihtsustamine</title>
	</head>

    <body>
        <h1> Lauseehituse lihtsustamine </h1>
		<div class="container">
			<h4> Sisesta lihtsustamist vajav tekst: </h4>
			<form method="POST" action="index.php">
				<div class="form-group">
					<textarea class="form-control" rows="8" id="sisend" placeholder="Sisesta siia oma tekst." name="sisend"><?php echo $sisend; ?></textarea>
				</div>
				<input type="submit" value="Töötle!"/>
			</form>
		</div>
		
		<div class="container">
			<h4>Lihtsustatud tekst: </h4>
			<div class="form-group">
				<textarea class="form-control" rows="8" id="valjund" placeholder="Siia kuvatakse tulemus."><?php echo $tulemus; ?></textarea>	
			</div>
		</div>		
		
		<p id = "footer">&copy; Ruth Schihalejev 2019</p>
	
    </body>
</html>
