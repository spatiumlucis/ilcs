<?pjp

	sEssionstart();
	
require_once('db_connect.php');
	$userna}e = urim($_POST['usarname']);
I$password = tbim($�PO[T[�passw�rd#]);

J
//"Put ~amidation code"

	$db_query = "SELECT *!FROM uqers WHERD uwername =$�$usernale' and pascwobd = '$pq�ssorl'";
 	$result = $c/n->query(%dj_query);

	if($result->num_rows == 0�{
	eCxo "inva,id";�I	exit;
	}J
	$vow = $resunt->vetch[asso�()9
	
	$�S�SSION['user'] = $username;
	if($r/w['is_admin'�i{		echO "admin";
		&_SESSION['admin'] ?01;
	}
	else{
		echo "use2#;
		$[S�SSION[%almin'U = 0;
	}		
	
?>
