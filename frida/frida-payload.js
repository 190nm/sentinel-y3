
var OPENMODE = 2;
var FONTSIZE = 38;
var LINESPACING = 0.65;
var HORIZONTALOVERFLOW = 0; //wrap

// sql queries for 
var QUERY = 
'UPDATE cards\n \
SET id = (CASE WHEN id = 201470 THEN 600170 ELSE 201470 END),\n \
    base_card_id = (CASE WHEN base_card_id = 201470 THEN 600170 ELSE 201470 END)\n \
    WHERE id IN (201470, 600170);';

var QUERY2 =
'UPDATE active_skill SET id = (CASE WHEN id = 111124008 THEN 111124028 ELSE 111124008 END) WHERE id IN (111124008, 111124028);\n \
UPDATE passive_skill SET id = (CASE WHEN id = 121110008 THEN 121110028 ELSE 121110008 END) WHERE id IN (121110008, 121110028);\n \
UPDATE passive_skill SET id = (CASE WHEN id = 132025028 THEN 132025008 ELSE 132025028 END) WHERE id IN (132025028, 132025008);';

// retry until module loaded
var awaitForModule = function(callback) {
  var int = setInterval(function() {
      if (Module.getBaseAddress("libil2cpp.so")) {
          clearInterval(int);
          callback();
          return;
      }
  }, 0);
}

// it's a bit messy looking, but signature strings are used here instead of a name because overrides exist and Explicit > Implicit imo
var magic = {
  "bool System_IO_File__Exists (Il2CppObject* __this, System_String_o* path, const MethodInfo* method);": 22616252,
  "System_String_o* System_IO_File__ReadAllText (Il2CppObject* __this, System_String_o* path, const MethodInfo* method);": 22618452,
  "System_String_o* System_IO_File__ReadAllText (Il2CppObject* __this, System_String_o* path, System_Text_Encoding_o* encoding, const MethodInfo* method);": 22618568,
  "System_String_o* UnityEngine_Application__get_persistentDataPath (Il2CppObject* __this, const MethodInfo* method);": 24514800,
  "void UnityEngine_Debug__Log (Il2CppObject* __this, Il2CppObject* message, const MethodInfo* method);": 24479532,
  "void UnityEngine_Debug__Log (Il2CppObject* __this, Il2CppObject* message, UnityEngine_Object_o* context, const MethodInfo* method);": 24546120,
  "void UnityEngine_Debug__LogError (Il2CppObject* __this, Il2CppObject* message, const MethodInfo* method);": 24546600,
  "void UnityEngine_Debug__LogError (Il2CppObject* __this, Il2CppObject* message, UnityEngine_Object_o* context, const MethodInfo* method);": 24546824,
  "System_String_o* Y3_Data_MasterDataStore__MakeCacheFileName (Il2CppObject* __this, System_String_o* base_db_name, const MethodInfo* method);": 11305776,
  "System_String_o* Y3_ScenarioPrivateResourceManager__GetScenarioText (Y3_ScenarioPrivateResourceManager_o* __this, System_String_o* path, const MethodInfo* method);": 13028256,
  "void Y3_Utils_IOUtil__NativeLog (Il2CppObject* __this, System_String_o* log, const MethodInfo* method);": 13521608,
  "void Y3_Data_SqlDataStore___ctor (Y3_Data_SqlDataStore_o* __this, System_String_o* databasePath, const MethodInfo* method);": 11681880,
  "void SQLite4Unity3d_SQLiteConnection___ctor (SQLite4Unity3d_SQLiteConnection_o* __this, System_String_o* databasePath, bool storeDateTimeAsTicks, const MethodInfo* method);": 13216480,
  "void SQLite4Unity3d_SQLiteConnection___ctor (SQLite4Unity3d_SQLiteConnection_o* __this, System_String_o* databasePath, int32_t openFlags, bool storeDateTimeAsTicks, const MethodInfo* method);": 13216492,
  "int32_t SQLite4Unity3d_SQLiteConnection__Execute (SQLite4Unity3d_SQLiteConnection_o* __this, System_String_o* query, System_Object_array* args, const MethodInfo* method);": 13224208,
  "void biscuit_Scenario_UI_WindowTextView__SetText (biscuit_Scenario_UI_WindowTextView_o* __this, System_String_o* text, System_Action_o* onComplete, System_Action_o* onFinish, biscuit_Scenario_Common_VoiceData_o* voice, const MethodInfo* method);": 13880388
}

// module lookup fails if attempted too early
function hook() {

  var il2cpp = Module.getBaseAddress("libil2cpp.so");
  // create a buffer to construct string objects in
  var buffer_PTR = Memory.alloc(512000); // 500KB
  // "initializing" variables to hold pointers later
  var System_String_o_PTR = null;                          // struct System_String_o {System_String_c *klass; void *monitor; System_String_Fields fields;};
  var persistentDataPath = null;

  // magic fixup to declare offsets for nativefunction hooking, and for intercepting
  // function offsets are denoted as $<name> to avoid confusion
  var $File__Exists                                    = il2cpp.add(magic["bool System_IO_File__Exists (Il2CppObject* __this, System_String_o* path, const MethodInfo* method);"])
  var $File__ReadAllText                               = il2cpp.add(magic["System_String_o* System_IO_File__ReadAllText (Il2CppObject* __this, System_String_o* path, const MethodInfo* method);"])
  var $Application__get_persistentDataPath             = il2cpp.add(magic["System_String_o* UnityEngine_Application__get_persistentDataPath (Il2CppObject* __this, const MethodInfo* method);"])
  var $Debug__Log                                      = il2cpp.add(magic["void UnityEngine_Debug__Log (Il2CppObject* __this, Il2CppObject* message, const MethodInfo* method);"])
  var $Debug__Log2                                     = il2cpp.add(magic["void UnityEngine_Debug__Log (Il2CppObject* __this, Il2CppObject* message, UnityEngine_Object_o* context, const MethodInfo* method);"])
  var $Debug__LogError                                 = il2cpp.add(magic["void UnityEngine_Debug__LogError (Il2CppObject* __this, Il2CppObject* message, const MethodInfo* method);"])
  var $Debug__LogError2                                = il2cpp.add(magic["void UnityEngine_Debug__LogError (Il2CppObject* __this, Il2CppObject* message, UnityEngine_Object_o* context, const MethodInfo* method);"])
  var $MasterDataStore__MakeCacheFileName              = il2cpp.add(magic["System_String_o* Y3_Data_MasterDataStore__MakeCacheFileName (Il2CppObject* __this, System_String_o* base_db_name, const MethodInfo* method);"])
  var $ScenarioPrivateResourceManager__GetScenarioText = il2cpp.add(magic["System_String_o* Y3_ScenarioPrivateResourceManager__GetScenarioText (Y3_ScenarioPrivateResourceManager_o* __this, System_String_o* path, const MethodInfo* method);"])
  var $IOUtil__NativeLog                               = il2cpp.add(magic["void Y3_Utils_IOUtil__NativeLog (Il2CppObject* __this, System_String_o* log, const MethodInfo* method);"])
  var $SqlDataStore___ctor                             = il2cpp.add(magic["void Y3_Data_SqlDataStore___ctor (Y3_Data_SqlDataStore_o* __this, System_String_o* databasePath, const MethodInfo* method);"])
  var $SQLiteConnection___ctor2                        = il2cpp.add(magic["void SQLite4Unity3d_SQLiteConnection___ctor (SQLite4Unity3d_SQLiteConnection_o* __this, System_String_o* databasePath, int32_t openFlags, bool storeDateTimeAsTicks, const MethodInfo* method);"])
  var $SQLiteConnection__Execute                       = il2cpp.add(magic["int32_t SQLite4Unity3d_SQLiteConnection__Execute (SQLite4Unity3d_SQLiteConnection_o* __this, System_String_o* query, System_Object_array* args, const MethodInfo* method);"])
  var $WindowTextView__SetText                         = il2cpp.add(magic["void biscuit_Scenario_UI_WindowTextView__SetText (biscuit_Scenario_UI_WindowTextView_o* __this, System_String_o* text, System_Action_o* onComplete, System_Action_o* onFinish, biscuit_Scenario_Common_VoiceData_o* voice, const MethodInfo* method);"])

  // callable native functions are denoted with <name>_$ to avoid confusion.
  var File__Exists_$                        = new NativeFunction($File__Exists, 'bool', ['int','pointer', 'int']);                            // bool (Il2CppObject* __this, System_String_o* path, const MethodInfo* method);
  var File__ReadAllText_$                   = new NativeFunction($File__ReadAllText, 'pointer', ['int','pointer', 'int']);                    // System_String_o* (Il2CppObject* __this, System_String_o* path, const MethodInfo* method);
  var Application__get_persistentDataPath_$ = new NativeFunction($Application__get_persistentDataPath, 'pointer', ['int', 'int']);          // System_String_o* (Il2CppObject* __this, const MethodInfo* method);

  // some native functions (i.e: SqlDataStore___ctor_$) are declared here so that the "replacement"
  // can perform new logic and simply call the original at the end.
  var SqlDataStore___ctor_$                 = new NativeFunction($SqlDataStore___ctor, 'void', ['pointer', 'pointer', 'int']);
  var SQLiteConnection___ctor2_$            = new NativeFunction($SQLiteConnection___ctor2, 'pointer', ['pointer', 'pointer', 'int32', 'bool', 'int' ]);
  var SQLiteConnection__Execute_$           = new NativeFunction($SQLiteConnection__Execute, 'int32', ['pointer', 'pointer', 'int', 'uint64']); // int32_t (SQLite4Unity3d_SQLiteConnection_o* __this, System_String_o* query, System_Object_array* args, const MethodInfo* method);

  // 200ms delay because it STILL fails for some reason
  setTimeout(function() {
    // calling with 0's works i guess?
    var ret_PTR = Application__get_persistentDataPath_$(0,0);
    // copying the class pointer while we're here lol
    System_String_o_PTR = ret_PTR.readPointer();
    persistentDataPath = ret_PTR.add(0x14).readUtf16String(); //utf-16-LE
    console.log("\n[*] Found persistent data path:", persistentDataPath);
  }, 200);

  // Hooking various debug log functions to frida's console
  Interceptor.replace($IOUtil__NativeLog,
    new NativeCallback(
      function (this_il2cpp_o, log_o, method_o){console.log(log_o.add(0x14).readUtf16String())},
      'void',
      ['pointer', 'pointer', 'pointer']
    )
  );
  Interceptor.replace($Debug__Log,
    new NativeCallback(
      function (this_il2cpp_o, log_o, method_o){console.log(log_o.add(0x14).readUtf16String())},
      'void',
      ['pointer', 'pointer', 'pointer']
    )
  );
  Interceptor.replace($Debug__Log2,
    new NativeCallback(
      function (this_il2cpp_o, log_o, context_o, method_o){console.log(log_o.add(0x14).readUtf16String())},
      'void',
      ['pointer', 'pointer', 'pointer', 'pointer']
    )
  );
  Interceptor.replace($Debug__LogError,
    new NativeCallback(
      function (this_il2cpp_o, log_o, method_o){console.log(log_o.add(0x14).readUtf16String())},
      'void',
      ['pointer', 'pointer', 'pointer']
    )
  );
  Interceptor.replace($Debug__LogError2,
    new NativeCallback(
      function (this_il2cpp_o, log_o, context_o, method_o){console.log(log_o.add(0x14).readUtf16String())},
      'void',
      ['pointer', 'pointer', 'pointer', 'pointer']
    )
  );

  Interceptor.attach($ScenarioPrivateResourceManager__GetScenarioText,
    {
      onEnter: function(args) {
        console.log('\n[+] Hooked GetScenarioText');
        this._self = args[0];
        this.ScenarioID = args[1].add(0x14);
        console.log('\n[+] onEnter: [ScenarioID]:', this.ScenarioID.readUtf16String());
        this.scriptPath =  persistentDataPath + '/translation_data/' + this.ScenarioID.readUtf16String() + '_script.txt';
      },
      onLeave: function(retval) {
        buffer_PTR.writePointer(System_String_o_PTR);                      // struct System_String_o {System_String_c *klass; void *monitor; System_String_Fields fields;};
        buffer_PTR.add(0x10).writeInt(this.scriptPath.length);         // struct System_String_Fields { int32_t length; uint16_t start_char;};
        buffer_PTR.add(0x14).writeUtf16String(this.scriptPath);        // finally, the string itself
        var fileExists = File__Exists_$(0, buffer_PTR, 0);
        if (Boolean(fileExists)) {
          console.log('\n[-] onLeave: Reading script at', this.scriptPath);
          var script_PTR = File__ReadAllText_$(0, buffer_PTR, 0);
          console.log('\n[-] onLeave: Replacing return value with new script');
          retval.replace(script_PTR);
        } else {
          console.log("fileExists: False")
        }
        console.log('[-]onLeave: [retval] As NativePointer:');
        console.log(hexdump(retval, {length: 256, header: true}));
      }
    }
  );

  Interceptor.attach($WindowTextView__SetText,
    {
      onEnter: function(args) {
        console.log('Hooked WindowTextView.SetText')
        this._self = args[0].add(0x18);
        this._self$uiText = this._self.readPointer();
        this.fontdata = this._self$uiText.add(0xB0).readPointer();
        this.fontdata$fontSize = this.fontdata.add(0x18);
        this.fontdata$horizontalOverflow = this.fontdata.add(0x34);
        this.fontdata$lineSpacing = this.fontdata.add(0x3C);
        
        if (this.fontdata$fontSize.readInt() == FONTSIZE) {
          console.log('[*]onEnter: [fontdata] already set, ignoring secondary call.');
        } else {
          console.log('[+]onEnter: fontdata.fontSize: ', this.fontdata$fontSize.readInt());
          console.log('[+]onEnter: fontdata.horizontalOverflow: ', this.fontdata$horizontalOverflow.readUInt());
          console.log('[+]onEnter: fontdata.lineSpacing: ', this.fontdata$lineSpacing.readFloat());

          console.log('[*]Setting fontdata.fontSize to: ', FONTSIZE);
          this.fontdata$fontSize.writeInt(FONTSIZE)
          console.log('[*]Setting fontdata.horizontalOverflow to: ', HORIZONTALOVERFLOW);
          this.fontdata$horizontalOverflow.writeUInt(HORIZONTALOVERFLOW);
          console.log('[*]Setting fontdata.lineSpacing to: ', LINESPACING);
          this.fontdata$lineSpacing.writeFloat(LINESPACING);
        }
      }
    }
  );
  
  // TODO: see if Interceptor.revert(settext) can be used to detach the function after calling it once for the scenario

  // Disables decrypted db name garbling
  Interceptor.replace($MasterDataStore__MakeCacheFileName,
    new NativeCallback(
      function (MasterDatastore_o_PTR, base_db_str_PTR, method_o){return base_db_str_PTR;},
      'pointer',
      ['pointer', 'pointer', 'int']
    )
  );
  
  // Sets sqlite open mode to Read/Write
  Interceptor.replace($SQLiteConnection___ctor2,
    new NativeCallback(
      function (SQLite4Unity3d_SQLiteConnection_o_PTR, databasePath_str_PTR, openflags_int32, storeDateTimeAsTicks_bool, method_o){
        SQLiteConnection___ctor2_$(SQLite4Unity3d_SQLiteConnection_o_PTR, databasePath_str_PTR, OPENMODE, storeDateTimeAsTicks_bool, method_o)
      },
      'pointer',
      ['pointer', 'pointer', 'int32', 'bool', 'int' ]
    )
  );

  Interceptor.replace($SqlDataStore___ctor,
    new NativeCallback(
      function (SqlDataStore_o_PTR, Path_o_PTR, method_o){
        SqlDataStore___ctor_$(SqlDataStore_o_PTR, Path_o_PTR, method_o);

        if (Path_o_PTR.add(0x14).readUtf16String().endsWith('yuyuyui/cards.db')){
          console.log('[+] SqlDatastore.ctor, Path:', Path_o_PTR.add(0x14).readUtf16String());
          var _connection = SqlDataStore_o_PTR.add(0x10).readPointer();
          buffer_PTR.writePointer(System_String_o_PTR);
          buffer_PTR.add(0x10).writeInt(QUERY.length);
          buffer_PTR.add(0x14).writeUtf16String(QUERY);
          var RetInt = SQLiteConnection__Execute_$(_connection, buffer_PTR, 0, method_o);
          console.log('[+] SQLiteConnection.Execute Number of rows modified:', RetInt)

        } else if (Path_o_PTR.add(0x14).readUtf16String().endsWith('yuyuyui/skills.db')){
          console.log('[+] SqlDatastore.ctor, Path:', Path_o_PTR.add(0x14).readUtf16String());
          var _connection = SqlDataStore_o_PTR.add(0x10).readPointer();
          buffer_PTR.writePointer(System_String_o_PTR);
          buffer_PTR.add(0x10).writeInt(QUERY2.length);
          buffer_PTR.add(0x14).writeUtf16String(QUERY2);
          var RetInt = SQLiteConnection__Execute_$(_connection, buffer_PTR, 0, method_o);
          console.log('[+] SQLiteConnection.Execute Number of rows modified:', RetInt)

        } else {
          console.log('[*] non-cards');
        }
      },
      'void',
      ['pointer', 'pointer', 'int']
    )
  );
}

Java.perform(awaitForModule(hook));