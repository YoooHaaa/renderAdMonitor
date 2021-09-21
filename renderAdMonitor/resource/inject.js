
// 1-监控中  2-正在加载
var JS_MONITOR = 1
var JS_LOAD    = 2

function sendData(sdk, event, status, msg){
    var packet = {
        'sdk'   : sdk,
        'event' : event,
        'status': status, 
        'msg'   : msg
    };
    send("ad:::" + JSON.stringify(packet));
}

function hook_func(classname, funcname, sdk, event){
    try{
        var Platform = Java.use(classname);
        var len = Platform[funcname].overloads.length;   
        for(var i = 0; i < len; ++i) {
            Platform[funcname].overloads[i].implementation = function () {    
                sendData(sdk, event, JS_LOAD, '');
                this[funcname].apply(this, arguments);
            }
        }  
        sendData(sdk, event, JS_MONITOR, '');
    }catch(error){
        //sendData(sdk, event, '监控失败', error);
    }
}

function discern_gdt(){
    //load广告的接口-广点通
    hook_func('com.qq.e.ads.nativ.NativeUnifiedAD', "$init", "广点通", "加载自渲染信息流广告");

    //设置点击view的接口-广点通
    hook_func('com.qq.e.ads.nativ.NativeUnifiedADDataAdapter', "bindAdToView", "广点通", "设置点击事件");
}

function discern_csj(){
    Java.enumerateLoadedClasses({
        onMatch: function (name, handle){
            if (name.indexOf("bytedance") != -1){
                var hookCls = Java.use(name);
                var interFaces = hookCls.class.getInterfaces();
                if(interFaces.length > 0){
                    //load广告的接口-穿山甲
                    if (interFaces[0].toString().indexOf("com.bytedance.sdk.openadsdk.TTAdNative") != -1){
                        var srevar = interFaces[0].toString();
                        if (srevar == "interface com.bytedance.sdk.openadsdk.TTAdNative"){
                            if (Java.use(name).class.isInterface() == false){
                                console.log("--> 实现类", name);
                                console.log("--> 接口类", interFaces[0].toString());
                                hook_func(name, "loadFeedAd",     "穿山甲", "加载自渲染信息流广告");
                                hook_func(name, "loadNativeAd",   "穿山甲", "加载自渲染插屏/Banner广告")
                                hook_func(name, "loadDrawFeedAd", "穿山甲", "加载自渲染Draw广告")
                            }
                        }
                    }

                    //设置点击view的接口-穿山甲
                    if (interFaces[0].toString().indexOf("com.bytedance.sdk.openadsdk.TTNativeAd") != -1){
                        var srevar = interFaces[0].toString();
                        if (srevar == "interface com.bytedance.sdk.openadsdk.TTNativeAd"){
                            if(Java.use(name).class.isInterface() == false){
                                console.log("--> 实现类", name);
                                console.log("--> 接口类", interFaces[0].toString());
                                hook_func(name, "registerViewForInteraction", "穿山甲", "设置点击事件")
                            }
                        }
                    }
                }
            }
        },
        onComplete: function () {
        }
    })
}

function monitor(){
    Java.perform(function(){
        discern_gdt();
        discern_csj();
    });
}

rpc.exports = {
    inject: function inject() {
        monitor();
    }
};