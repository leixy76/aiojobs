import asyncio
from unittest import mock

import pytest


async def test_job_spawned(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    assert job.active
    assert not job.closed
    assert not job.pending
    assert 'closed' not in repr(job)
    assert 'pending' not in repr(job)


async def test_job_awaited(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    await job.wait()

    assert not job.active
    assert job.closed
    assert not job.pending
    assert 'closed' in repr(job)
    assert 'pending' not in repr(job)


async def test_job_closed(scheduler):
    async def coro():
        pass
    job = await scheduler.spawn(coro())
    await job.close()

    assert not job.active
    assert job.closed
    assert not job.pending
    assert 'closed' in repr(job)
    assert 'pending' not in repr(job)


async def test_job_pending(make_scheduler):
    scheduler = make_scheduler(limit=1)

    async def coro1():
        await asyncio.sleep(10)

    async def coro2():
        pass

    await scheduler.spawn(coro1())
    job = await scheduler.spawn(coro2())

    assert not job.active
    assert not job.closed
    assert job.pending
    assert 'closed' not in repr(job)
    assert 'pending' in repr(job)


# Mangle a name for satisfy 'pending' not in repr check
async def test_job_resume_after_p_e_nding(make_scheduler):
    scheduler = make_scheduler(limit=1)

    async def coro1():
        await asyncio.sleep(10)

    async def coro2():
        pass

    job1 = await scheduler.spawn(coro1())
    job2 = await scheduler.spawn(coro2())

    await job1.close()

    assert job2.active
    assert not job2.closed
    assert not job2.pending
    assert 'closed' not in repr(job2)
    assert 'pending' not in repr(job2)


async def test_job_wait_result(make_scheduler):
    handler = mock.Mock()
    scheduler = make_scheduler(exception_handler=handler)

    async def coro():
        return 1

    job = await scheduler.spawn(coro())
    ret = await job.wait()
    assert ret == 1
    assert not handler.called


async def test_job_wait_exception(make_scheduler):
    handler = mock.Mock()
    scheduler = make_scheduler(exception_handler=handler)
    exc = RuntimeError()

    async def coro():
        raise exc

    job = await scheduler.spawn(coro())
    with pytest.raises(RuntimeError) as ctx:
        await job.wait()
    assert ctx.value is exc
    assert not handler.called


async def test_job_cancel_dont_raise(make_scheduler):
    handler = mock.Mock()
    scheduler = make_scheduler(exception_handler=handler)
    exc = RuntimeError()
    fut1 = asyncio.Future()
    fut2 = asyncio.Future()
    fut3 = asyncio.Future()

    async def coro():
        await fut1
        fut2.set_result(None)
        await fut3
        raise exc

    job = await scheduler.spawn(coro())
    fut1.set_result(None)
    await fut2
    fut3.set_result(None)

    await job.close()
    handler.assert_called_with()

