from typing import List, Dict, Any

from linebot.v3.messaging.models import(
        FlexMessage,
        CarouselContainer,
        BubbleContainer,
        BoxComponent,
        TextComponent,
        ImageComponent,
        ButtonComponent,
        URIAction
)

def build_restaurant_carousel(shops: List[Dict[str, Any]]) -> FlexMessage:
    bubbles: List[BubbleContainer] = []

    for shop in shops:
        shop_name = shop.get('name','---')
        genre_name = shop.get('genre').get('catch','---')
        budget = shop.get('budget',{}).get('average','---')
        open_datetime = shop.get('open','---')
        close_datetime = shop.get('close','---')
        url = shop.get('urls').get('pc','https://hotpepper.jp/')
        image_url = shop.get('photo',{}).get('pc',{}).get('m',"")

        hero = ImageComponent(
            url = image_url,
            size = "full",
            aspect_ratio = "20:13",
            aspect_mode = "cover",
            )
        body = BoxComponent(
            layout = "vertical",
            spacing = "md",
            contents = [
                TextComponent(text = shop_name, weight = "bold", size = "xl", wrap = True),
                TextComponent(text = f"ジャンル:{genre_name} | 予算:{budget}", size = "sm"),
                TextComponent(text = open_datetime, size = "sm", wrap = True),
                ]
            )
        footer = BoxComponent(
            layout = "vertical",
            spacing = "sm",
            contents = [
                ButtonComponent(
                    style = "primary",
                    action = URIAction(label = "詳細を見る", uri = url),
                    color = "#FF5B5B",
                    ),
                ]
            )
    
        bubbles.append(bubble)

        if len(bubbles) >= 5:
            break

    carousel = CarouselContainer(contents = bubbles)

    return FlexMessage(alt_text = "おすすめのお店", contents = carousel)

