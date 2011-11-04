google.load("jquery","1.6.2");

google.setOnLoadCallback(
        function(){
            $(document).ready(function(){T.init();T.poll();});
        }
        );
var T = {
    cursor: false,
    types:['hashtags','retweets','ats','links']
};

T.init = function(){
    $('input[type=checkbox]').click(T.click);
};

T.click = function(ev){
    if(ev.target.id == 'all'){
        for(i in T.types)
            $('#' + T.types[i].attr('checked',$('#all').attr('checked'));
    }
    else
        $('#all').attr('checked',false);
        
};

T.poll = function(){
    var args = {};
    if(T.cursor) args.cursor = T.cursor;
    $.ajax({
            url:"/updates",
            type:"POST",
            dataType:"json",
            data:$.param(args),
            success:T.new_tweets
    });
};

T.new_tweets = function(response){
    if(!T.cursor)
        $('#waiting').remove();

    T.cursor = response.tweets[response.tweets.length - 1].id;

    for(var i = 0; i < response.tweets.length; ++i){
        if(T.should_show_tweet(response.tweets[i])){
            var d = $(response.tweets[i].html);
            d.css('display','none');
            $('#content').prepend(d);
            d.slideDown();
        }
    }
    //clean up the DOM
    var limit = 100;
    var messages = $('.message');
    for(var x = messages.length-1;x>limit; --x)
        $(messages[x]).remove();

    T.poll();
};

T.should_show_tweet = function(tweet){
    $('#all-count').text(parseInt($('#all-count').text()) + 1);
    
    var show_tweet = false;

    for(x in T.types){
        var type = T.types[x];

        //does the tweet have the specified type?
        if(tweet.stats[type].length){
            //does the user want to see it?
            if($("#"+type).attr('checked'))
                show_tweet = true;

            var count_div = $('#' + type + '-count');
            count_div.text(parseInt(count_div.text())+1);
        }
    }
    return show_tweet;
};
                    
