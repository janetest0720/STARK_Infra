#STARK Code Generator component.
#Produces the customized static content for a STARK system

#Python Standard Library
import textwrap
import os

#Private modules
import convert_friendly_to_system as converter

def create(data):

    api_endpoint = data['API Endpoint']
    entities     = data['Entities']
    bucket_name  = data['Bucket Name']
    region_name  = os.environ['AWS_REGION']

    source_code = f"""\
        api_endpoint_1 = '{api_endpoint}'

        const STARK={{
            'auth_url':`${{api_endpoint_1}}/stark_auth`,
            'login_url':`${{api_endpoint_1}}/login`,
            'logout_url':`${{api_endpoint_1}}/logout`,
            'sys_modules_url':`${{api_endpoint_1}}/sys_modules`,"""

    #Each entity is a big module, has own endpoint
    for entity in entities:
        entity_endpoint_name = converter.convert_to_system_name(entity)
        source_code += f"""
            '{entity_endpoint_name}_url':`${{api_endpoint_1}}/{entity_endpoint_name}`,"""

    #STARK-provided common methods go here
    source_code += f"""
            'STARK_User_url':`${{api_endpoint_1}}/STARK_User`,
            'STARK_Module_url':`${{api_endpoint_1}}/STARK_Module`,
            'STARK_User_Roles_url':`${{api_endpoint_1}}/STARK_User_Roles`,
            'STARK_User_Permissions_url':`${{api_endpoint_1}}/STARK_User_Permissions`,
            'STARK_User_Sessions_url':`${{api_endpoint_1}}/STARK_User_Sessions`,
            'STARK_Module_Groups_url':`${{api_endpoint_1}}/STARK_Module_Groups`,
            'methods_with_body': ["POST", "DELETE", "PUT"],
            'bucket_name': '{bucket_name}',
            'region_name': '{region_name}',
            'file_ext_whitelist': ['jpg','jpeg','gif','bmp','png',
                                'doc','docx','xls','xlsx','ppt','pptx', 'csv',
                                'odt','ods','odp','txt','rtf','pdf',
                                'zip','rar','7z','bz2','tar','gz'],
            'max_upload_size': 10,//in MB,
            'local_storage_item_ttl': 1, //in minutes
            'local_storage_permission_ttl': 360,
            'local_storage_listview_ttl': 10,

            request: function(method, fetchURL, payload='') {{

                let fetchData = {{
                    mode: 'cors',
                    headers: {{ "Content-Type": "application/json" }},
                    method: method,
                    credentials: 'include'
                }}

                if(this.methods_with_body.includes(method)) {{
                    console.log("stringifying payload")
                    console.log(payload)
                    fetchData['body'] = JSON.stringify(payload)
                }}

                return fetch(fetchUrl, fetchData).then( function(response) {{
                    if (!response.ok) {{
                        console.log(response)

                    //Specific indicators to watch for:
                    //401 (Unauthorized)= AWS API Gateway Authorizer error, missing Identity Source in request. Redirect to login screen
                    //403 (Forbidden) = Identity Source (cookie) was submitted, but Authorizer determined it was invalid. Redirect to home page
                    if (response.status == 401) {{
                        console.log("Unauthenticated request, redirecting to Login Screen")
                        window.location.href="index.html"
                    }}
                    if (response.status == 403) {{
                        console.log("Forbidden request, redirecting to Home Page")
                        window.location.href="home.html"
                        //FIXME: Redirecting to home for 403 errors could cause problems during cookie expiration (default: 12hrs.
                        //  Might be best to just immediately call logout to clear problematic session id and redirect to login?
                        //      See if this is a real problem first, though. Currently our Authorizer really only cares about being logged in,
                        //      and does not really do granular permissions checking (and having cached response could complicate having granular,
                        //      per-module permissions checking there, unless these granular items also get added to Identity Sources so they are all cached
                        //      independently.)
                        //  If browser clears local cookies earlier than DDB TTL execution, then this won't be a problem at all, as 401 will be triggered instead of
                        //  403. Browser clearing local cookie faster than DDB TTL execution is practically guaranteed, as TTL execution is not guaranteed real time.
                    }}

                        throw Error("Probably an auth failure from STARK SEC");
                    }}
                    return response
                }}).then((response) => response.json())
            }},

            logout: function () {{
                var sys_exit = confirm("Log out?");
                
                if(sys_exit) {{
                    console.log("Log out command!")
                    loading_modal.show()
                    fetchUrl = STARK.logout_url
                    payload={{}}
                    STARK.request('POST', fetchUrl, payload).then( function(data) {{
                            loading_modal.hide()
                            console.log("Server-side log out successful!");
                            window.location.href = "index.html";
                    }})
                    .catch(function(error) {{
                        console.log("Encountered an error! [" + error + "]")
                        loading_modal.hide()
                    }});
                }}
            }},
            auth: function(payload) {{
                fetchUrl = STARK.auth_url
                return STARK.request('POST', fetchUrl, payload)
            }},
            create_UUID: function() {{
                var dt = new Date().getTime();
                var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
                    var r = (dt + Math.random()*16)%16 | 0;
                    dt = Math.floor(dt/16);
                    return (c=='x' ? r :(r&0x3|0x8)).toString(16);
                }});
                return uuid;
            }},
            get_s3_credentials: function(){{
                fetchUrl = STARK.auth_url
                return this.request('POST', fetchUrl, {{'rt': 's3'}})
            }},
            get_file_ext_whitelist: function(field_settings, table_settings = "", mode="overwrite") {{
                //two modes: overwrite = overwrites the whitelist in the following order: field defined > table defined > globally defined
                //           mix       = combines the all the whitelist
                whitelist = ""
                global_settings = STARK.file_ext_whitelist.join(', ')
                if(mode == "overwrite")
                {{
                    whitelist = field_settings == "" ? table_settings == "" ? global_settings : table_settings : field_settings
                }}
                else if (mode == "mix")
                {{
                    whitelist = table_settings == "" ? global_settings: table_settings

                    if(field_settings != "")
                    {{
                        whitelist.concat(`, ${{field_settings}}`)
                    }}

                }}
                return whitelist
            }},
            get_allowed_upload_size: function(field_settings, table_settings = 0) {{
                global_settings = STARK.max_upload_size
                size_setting = field_settings == 0 ? table_settings == 0 ? global_settings : table_settings : field_settings;
                conversion = size_setting * 1024 * 1024
                return conversion
            }},

            set_page_permissions: function () {{
                loading_modal.show();
                console.log("Hello")
                root.auth_config = {{
                    'View': [root.auth_list.View.permission],
                    'Add': [root.auth_list.Add.permission],
                    'Delete': [root.auth_list.Delete.permission],
                    'Edit': [root.auth_list.Edit.permission],
                    'Report': [ 
                                root.auth_list.Report.permission, 
                                root.auth_list.Edit.permission, 
                                root.auth_list.Delete.permission 
                            ],
                    'ListView': [ 
                                root.auth_list.Report.permission, 
                                root.auth_list.Edit.permission, 
                                root.auth_list.Delete.permission, 
                                root.auth_list.Add.permission, 
                                root.auth_list.View.permission
                            ]
                }}
            }},

            check_permission: function (data) {{
                console.log("Checking")
                console.log(data)
                STARK.auth({{'stark_permissions': data}}).then( function(data) {{
                    console.log(data)
                    console.log("Auth Request Done!");
                    console.log(data);


                    for (var permission of Object.keys(data)) {{
                        console.log(permission + " -> " + data[permission])

                        for (var key of Object.keys(root.auth_list)) {{
                            /*Find a math in auth_list for our current STARK permission key*/
                            if (root.auth_list[key]['permission'] == permission) {{
                                root.auth_list[key]['allowed'] = data[permission]
                            }}
                        }}
                    }}
                    loading_modal.hide()
                }})
                .catch(function(error) {{
                    console.log("Encountered an error! [" + error + "]")
                    alert("Request Failed: System error or you may not have enough privileges")
                    loading_modal.hide()
                }});
            }},

            validate_form: function (metadata, form_to_validate, form_upload ="")
            {{
                var is_valid_form = true;
                
                for (var form_element of Object.keys(metadata)) {{
                    let value = form_to_validate[form_element]
                    let md_element = metadata[form_element]
                    let message = ""
                    // loop through meta data per element)
                    md_element['feedback'] = ""
                    md_element['state'] = true
                    
                    //required
                    if(md_element['required']) {{
                        if(md_element['data_type'] == 'file-upload' ) {{ //need to change checking since file-upload is better to be determined by their upload progress
                            if (form_upload[form_element]['progress_bar_val'] != 100)
                            {{  
                                message = `${{message}} is required`
                            }}
                        }}
                        else {{
                            if(value == "") {{
                                message = `${{message}} is required`
                            }}
                        }}
                    }}

                    if(message == "") {{
                        //maxlength
                        if(md_element['max_length'] != "") {{
                            if(value.length > md_element['max_length']) {{
                                message = ` must not exceed ${{md_element['max_length']}} characters`
                            }}
                        }}
                        
                        //data type
                        if(md_element['data_type'] != '') {{
                            if(md_element['data_type'] == 'number') {{
                                parsed_value = Number(value)
                                if(isNaN(value)) {{
                                    message= ` only accepts numerical values`
                                }}
                            }}
                            else if(md_element['data_type'] == 'boolean') {{
                                if (value !== true || value !== false) {{
                                    message= ` only accepts True or False`
                                }}
                            }}
                            else if (md_element['data_type'] == 'string') {{
                                if(typeof value != 'string') {{
                                    message= ` only accepts string values`
                                }}
                            }}
                        }}
                    }}
                
                    if (message != "") {{
                        md_element['feedback'] = `This field${{message}}`
                        md_element['state'] = false
                        is_valid_form = false
                    }}
                    
                }}
                // console.log(metadata)
                return {{'is_valid_form':is_valid_form, 'new_metadata': metadata}}
            }},

            set_local_storage_item: function(item, key, data, ttl_in_min="") {{
                var item_ttl = ''

                if(item == 'Permissions') {{
                    item_ttl = this.local_storage_permission_ttl
                }}
                else if (item == 'Listviews') {{
                    item_ttl = this.local_storage_listview_ttl
                }}
                else {{
                    item_ttl = ttl_in_min == "" ? this.local_storage_item_ttl : ttl_in_min
                }}
                
                var expiry_time = Date.now() + (1000 * 60 * item_ttl)
                console.log(`${{item}}: ${{key}} expiry:`, new Date(expiry_time))
                
                //check item first if there is already a stored data to avoid overwriting
                var temp = JSON.parse(localStorage.getItem(item))
                console.log(temp)
                var data_to_store = {{}}
                data_to_store[`${{key}}`] = {{'data': data}}
                data_to_store[`${{key}}`]['expiry_time'] = expiry_time
                localStorage.setItem(item, JSON.stringify({{ ...temp, ...data_to_store}}))

            }},

            get_local_storage_item: function(item, key) {{
                // returns false or the requested stored data
                fetched_data = JSON.parse(localStorage.getItem(item))
                if(fetched_data) {{
                    arr_keys = Object.keys(fetched_data)
                    if(arr_keys.filter(elem => elem == key).length > 0) {{
                        var expiry_time = fetched_data[key]['expiry_time']
                        if(Date.now() < expiry_time) {{
                            return fetched_data[key]['data']
                        }}
                        // localStorage.removeItem only deletes the 'item' of the storage,
                        // it can't select deeper in the object stored in the 'item'. 
                        // but since we fetched the entire item we can create a workaround
                        // 1. Assign the data from storage in fetched_data
                        // 2. Trigger removeItem for the selected item to remove everything
                        // 3. Remove the key that expires from the fetched_data
                        // 4. Trigger setItem again using the fetched_data
            
                        localStorage.removeItem(item)
                        delete fetched_data[key]
                        localStorage.setItem(item,JSON.stringify(fetched_data))
                        console.log(`${{item}} ${{key}} expired.. fetch again.`)
                    }}
                    
                }}
                else {{
                    console.log(`${{item}} ${{key}} not yet set.`)

                }}
                
                return false
            }},

        }};"""

    return textwrap.dedent(source_code)
