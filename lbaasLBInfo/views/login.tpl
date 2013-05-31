<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
	<LINK href="static/style.css" type=text/css rel=stylesheet>
	<LINK href="static/forms.css" type=text/css rel=stylesheet>
	<LINK href="static/lists.css" type=text/css rel=stylesheet>
	<LINK href="static/polls.css" type=text/css rel=stylesheet>
    </head>
    <body>
<center>
				<table cellSpacing="0" borderColorDark="white" cellPadding="2" borderColorLight="#a6a3de" border="1">
				<tr>
					<th vAlign="bottom" bgColor="#eeeffd" colspan="2"><img src=static/CLB.png /><br>Login</th>
				</tr>
				<FORM id=login_form name=login_form action="/login" method=post>
				<TR>
					<TD width="128" class=sideboxtext>
						<center>
						Username:&nbsp;
						<INPUT class=field_textbox maxLength=20 size=15 name=name>
						</center>
					</TD>
					<TD width="128" class=sideboxtext>
						<center>
						Password:&nbsp;
						<INPUT class=field_textbox type=password maxLength=20 size=15 name=password
						</center>
					 </TD>
				</TR>
				%if failed == 'fail':
				    <TR>
                                        <Th height="29" align="middle" class=sideboxtext bgColor="#eeeffd" colspan="2">
                                                <FONT COLOR=RED><B>Login Failed</B></FONT>
                                        </Th>
                                    </TR>
				%end
				<TR>
					<Th height="29" align="middle" class=sideboxtext bgColor="#eeeffd" colspan="2">
						<INPUT class=button type=submit value=Login name=action>
					</Th>
				</TR>
				</FORM>
				</TABLE>
				</center>
	
    </body>
</html>

