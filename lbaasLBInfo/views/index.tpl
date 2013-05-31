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
                                        <th vAlign="bottom" bgColor="#eeeffd" colspan=2><img src=static/CLB.png /><br>Loadbalancer Lookup</th>
                                </tr>
				<FORM id=login_form name=login_form action="/" method=post>
				<TR>
					<TD class=sideboxtext>
						<center>Loadbalancer ID:&nbsp;
						<INPUT class=field_textbox maxLength=10 size=10 name=lbid></center>
					</TD>
					<TD class=sideboxtext>
						<center>Located in DC:&nbsp;
                                                <select name="dc">
                                                	<option value="ord1" selected="selected">ORD1</option>
                                                	<option value="dfw1">DFW1</option>
                                                	<option value="lon3">LON3</option>
                                                </select>
						</center>
                                         </TD>
				</TR>
                                %if lbidvalidated == 'unknown':
                                    <TR>
                                        <Th height="29" align="middle" class=sideboxtext bgColor="#eeeffd" colspan=2>
                                                <FONT COLOR=RED><B>Unknown LB!</B></FONT>
                                        </Th>
                                    </TR>
                                %end
				<TR>
					<Th height="29" align="middle" class=sideboxtext bgColor="#eeeffd" colspan=2>
						<INPUT class=button type=submit value=Search name=action>
					</Th>
				</TR>
				</FORM>
				</TABLE>
				</center>
	
    </body>
</html>

