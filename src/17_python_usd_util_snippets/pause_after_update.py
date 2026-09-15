import asyncio
import omni.kit.app
import omni.timeline


async def pause_after_update():
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    await omni.kit.app.get_app().next_update_async()
    timeline.pause()
    print(
        "Paused after one application update; current time:",
        timeline.get_current_time(),
    )


pause_task = asyncio.ensure_future(pause_after_update())
pause_task.add_done_callback(lambda task: task.result())
