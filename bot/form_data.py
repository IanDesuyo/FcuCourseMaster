# Simulate postback payload

LOGIN = {
    "__EVENTTARGET": "ctl00$Login1$LoginButton",
    "__EVENTARGUMENT": "",
    "__VIEWSTATEENCRYPTED": "",
    "__LASTFOCUS": "",
    # "ctl00$Login1$UserName": {username},
    # "ctl00$Login1$Password": {password},
    # "ctl00$Login1$vcode": {verify_code},
    "ctl00$Login1$RadioButtonList1": "zh-tw",
    "ctl00$temp": "",
}

BASIC_STATE = {
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__SCROLLPOSITIONX": "0",
    "__SCROLLPOSITIONY": "0",
    "__VIEWSTATEENCRYPTED": "0",
    "ctl00_ToolkitScriptManager1_HiddenField": "",
    "ctl00_MainContent_TabContainer1_ClientState": '{"ActiveTabIndex":1,"TabState":[true,true,true]}',
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlDegree": "1",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlDept": "",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlUnit": "",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlClass": "",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlWeek": "",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlPeriod": "",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbCourseName": "",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbTeacherName": "",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlUseLanguage": "01",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlSpecificSubjects": "1",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$cbShowSelected": "on",
    "ctl00$MainContent$TabContainer1$tabSelected$tbSubID": "",
    "ctl00$MainContent$TabContainer1$tabSelected$cpeWishList_ClientState": "false",
}

SEARCH_COURSE = {
    **BASIC_STATE,
    "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$btnSearchOther",
    "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$cbOtherCondition1": "on",
    # "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbSubID": {course_id}
}

WISHLIST_SEARCHED_COURSE = {
    **BASIC_STATE,
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    # "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$gvSearchResult$ctl{index}$btnAdd": "關注",
}

DIRECT_SEARCH_COURSE = {
    **BASIC_STATE,
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "ctl00_MainContent_TabContainer1_ClientState": '{"ActiveTabIndex":2,"TabState":[true,true,true]}',
    # "ctl00$MainContent$TabContainer1$tabSelected$tbSubID": {course_id},
    "ctl00$MainContent$TabContainer1$tabSelected$btnGetSub": "查詢",
}

SELECT_DIRECT_SEARCHED_COURSE = {
    **BASIC_STATE,
    "ctl00_MainContent_TabContainer1_ClientState": '{"ActiveTabIndex":2,"TabState":[true,true,true]}',
    "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabSelected$gvToAdd",
    "__EVENTARGUMENT": "addCourse$0",
}


SELECT_FROM_WISHLIST = {
    **BASIC_STATE,
    # "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabSelected$gvWishList$ctl{index}$btnAdd",
    "__EVENTARGUMENT": "",
}


REMOVE_WISHLIST = {
    **BASIC_STATE,
    # "__EVENTTARGET": "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$gvSearchResult$ctl{index}$btnRemove",
    "__EVENTARGUMENT": "",
    "ctl00_MainContent_TabContainer1_ClientState": '{"ActiveTabIndex":2,"TabState":[true,true,true]}',
}