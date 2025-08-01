# FcuCourseMaster 逢甲幹課大師

> [!WARNING]  
> 本專案已不再維護，且選課系統多次更新，多數功能已無法正常使用。

## Why

![how-to-select-course](/docs/how-to.png)

手動加退選課程一直是逢甲學生需要浪費時間在做的事，從大一到大四再幸運至少也要搶個 2 次課，我相信每個人都希望能有一個機器人幫助自己選到想要的課。

開源本專案的目的是希望校方能改善選課流程，透過抽選的方式替代手動加退選，讓學生能夠更公平地選到自己想要的課程。

本人並沒有因開發此程式而獲得任何利益，也沒有因此交到女朋友。

## Install

1. Clone this repository
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

## Usage

> [!WARNING]
> 執行此程式即代表同意自行承擔使用此程式所帶來的風險，本人不會對任何因使用此程式而導致的損失負責。

要執行 FcuCourseMaster，請參考 [main.py](main.py) 的做法建立 `FcuCourseMaster` instance，並呼叫 `async start()` 來啟動。

[multi_account.py](multi_account.py) 展示了多帳號範例，用以節省監控相同課程時的請求時間。

### FcuCourseMaster class

Main logic of the bot.

```python
bot = FcuCourseMaster(
    username="D1234567",
    password="password",
    target_courses=[
        TargetCourse("1234", 2, True),
    ],
)

# Run the bot
asyncio.get_event_loop().run_until_complete(bot.start())
```

### TargetCourse class

Represents the course you want to select.

```python
target_course = TargetCourse(
    course_id="1234", # Course ID
    credit=2, # Credit of the course
    use_wishlist=True, # Add course to the wishlist, which will be faster than the original, but the same period cannot be selected or wishlisted for other courses. Defaults to False.
)
```

### SearchOption class

Defines the options when using coursesearch.fcu.edu.tw API.

By default, it should automatically detect the semester and year, but you can specify them manually.

```python
search_option = SearchOption(
    lang=SearchLang.CHINESE, # Language of the search result
    sms=Semester.FIRST, # Semester of the search result
    year=2024, # Year of the search result
    timeout=ClientTimeout(total=2), # Timeout for requests
    delay=1 # Delay between each course quota check. In theory, you can set it to 0, but it may cause the server to block your IP.
)
```

### Notification class

Defines the notification webhook when a course is successfully selected.

```python
bot = FcuCourseMaster(
    ...
    notification_webhook="https://discord.com/api/webhooks/xxx",
)
```

## Acknowledgements

[Dcard 上的匿名資工系同學](https://www.dcard.tw/f/fcu/p/236946822)
