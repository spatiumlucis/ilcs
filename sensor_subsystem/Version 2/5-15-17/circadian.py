import subprocess
import socket
import MySQLdb

def init_circadian_table():
    """
    This function is used for creating the master
    circadian table. The table is a list that has
    1440 locations (1 for each minute of the day).
    Each location is also a list of R, G, B brightness
    values.The value depends on what time of day is is.
    Between different ranges of time there are different
    linear functions for the brightness values.
    NOTE: This table is calculated for a person that wakes
    up at 7AM (420 min) and goes to sleep at 11 PM (1380 min).

    :return: None
    """
    """
    Import global MASTER_CIRCADIAN_TABLE so that it can be edited
    """
    MASTER_CIRCADIAN_TABLE = []

    colors = []
    offsets = []

    t = 0
    while t < 1440:
        """
        The colors list is always filled in the order R, G, B.
        Afterwards it is appended to the MASTER_CIRCADIAN_TABLE
        """
        if t >= 300 and t <= 420:

            colors.append((((135.0 / 120) * t - 337.5) / 255) * 100)

            colors.append((((206.0 / 120) * t - 515) / 255) * 100)

            colors.append((((250.0 / 120) * t - 625) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []

        elif t >= 420 and t <= 720:
            colors.append((((120.0 / 300) * t - 33) / 255) * 100)

            colors.append((((49.0 / 300) * t + 137.4) / 255) * 100)

            colors.append((((5.0 / 300) * t + 243) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)

            colors = []

        elif t >= 720 and t <= 1140:
            colors.append((((-2.0 / 420) * t + 258.429) / 255) * 100)

            colors.append((((-161.0 / 420) * t + 531) / 255) * 100)

            colors.append((((-172.0 / 420) * t + 549.857) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)

            colors = []

        elif t >= 1140 and t <= 1380:

            colors.append((((-253.0 / 240) * t + 1454.75) / 255) * 100)

            colors.append((((-94.0 / 240) * t + 540.5) / 255) * 100)

            colors.append((((-83.0 / 240) * t + 477.25) / 255) * 100)

            MASTER_CIRCADIAN_TABLE.append(colors)

            colors = []

        else:
            colors.append(0)

            colors.append(0)

            colors.append(0)

            MASTER_CIRCADIAN_TABLE.append(colors)
            colors = []

        t += 1
    return MASTER_CIRCADIAN_TABLE

def init_offset_table():
    MASTER_OFFSET_TABLE = []
    offsets = []
    t = 0
    while t < 1440:
        offsets.append(0)
        offsets.append(0)
        offsets.append(0)
        MASTER_OFFSET_TABLE.append(offsets)
        offsets = []
        t += 1
    init_red_offset(MASTER_OFFSET_TABLE)
    init_green_offset(MASTER_OFFSET_TABLE)
    init_blue_offset(MASTER_OFFSET_TABLE)
    return MASTER_OFFSET_TABLE

def init_red_offset(MASTER_OFFSET_TABLE):
    #global MASTER_OFFSET_TABLE
    t = 0
    while t < 1440:
        if t >= 313 and t <= 323:
            MASTER_OFFSET_TABLE[t][0] = 0
        elif t >= 323 and t <= 325:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 161.5
        elif t >= 325 and t <= 329:
            MASTER_OFFSET_TABLE[t][0] = 1
        elif t >= 329 and t <= 331:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 163.5
        elif t >= 331 and t <= 333:
            MASTER_OFFSET_TABLE[t][0] = 2
        elif t >= 333 and t <= 335:
            MASTER_OFFSET_TABLE[t][0] = t - 331
        elif t >= 335 and t <= 337:
            MASTER_OFFSET_TABLE[t][0] = 4
        elif t >= 337 and t <= 339:
            MASTER_OFFSET_TABLE[t][0] = t - 333
        elif t >= 339 and t <= 343:
            MASTER_OFFSET_TABLE[t][0] = 6
        elif t >= 343 and t <= 345:
            MASTER_OFFSET_TABLE[t][0] = t - 337
        elif t >= 345 and t <= 347:
            MASTER_OFFSET_TABLE[t][0] = 8
        elif t >= 347 and t <= 349:
            MASTER_OFFSET_TABLE[t][0] = t - 339
        elif t >= 349 and t <= 351:
            MASTER_OFFSET_TABLE[t][0] = 10
        elif t >= 351 and t <= 353:
            MASTER_OFFSET_TABLE[t][0] = t - 341
        elif t >= 353 and t <= 355:
            MASTER_OFFSET_TABLE[t][0] = 12
        elif t >= 355 and t <= 357:
            MASTER_OFFSET_TABLE[t][0] = t - 343
        elif t >= 357 and t <= 359:
            MASTER_OFFSET_TABLE[t][0] = 14
        elif t >= 359 and t <= 363:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 363 and t <= 365:
            MASTER_OFFSET_TABLE[t][0] = t - 347
        elif t >= 365 and t <= 367:
            MASTER_OFFSET_TABLE[t][0] = 18
        elif t >= 367 and t <= 369:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 369 and t <= 371:
            MASTER_OFFSET_TABLE[t][0] = t - 350
        elif t >= 371 and t <= 373:
            MASTER_OFFSET_TABLE[t][0] = 21
        elif t >= 373 and t <= 375:
            MASTER_OFFSET_TABLE[t][0] = t - 352
        elif t >= 375 and t <= 379:
            MASTER_OFFSET_TABLE[t][0] = 23
        elif t >= 379 and t <= 381:
            MASTER_OFFSET_TABLE[t][0] = t - 356
        elif t >= 381 and t <= 383:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 383 and t <= 385:
            MASTER_OFFSET_TABLE[t][0] = t - 357
        elif t >= 385 and t <= 387:
            MASTER_OFFSET_TABLE[t][0] = 28
        elif t >= 387 and t <= 389:
            MASTER_OFFSET_TABLE[t][0] = t - 359
        elif t >= 389 and t <= 391:
            MASTER_OFFSET_TABLE[t][0] = 30
        elif t >= 391 and t <= 393:
            MASTER_OFFSET_TABLE[t][0] = t - 361
        elif t >= 393 and t <= 395:
            MASTER_OFFSET_TABLE[t][0] = 32
        elif t >= 395 and t <= 397:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 165.5
        elif t >= 397 and t <= 399:
            MASTER_OFFSET_TABLE[t][0] = t - 364
        elif t >= 399 and t <= 401:
            MASTER_OFFSET_TABLE[t][0] = 35
        elif t >= 401 and t <= 403:
            MASTER_OFFSET_TABLE[t][0] = t - 366
        elif t >= 403 and t <= 405:
            MASTER_OFFSET_TABLE[t][0] = 0.5 * t - 164.5
        elif t >= 405 and t <= 407:
            MASTER_OFFSET_TABLE[t][0] = 1.5 * t - 569.5
        elif t >= 407 and t <= 411:
            MASTER_OFFSET_TABLE[t][0] = 41
        elif t >= 411 and t <= 413:
            MASTER_OFFSET_TABLE[t][0] = t - 370
        elif t >= 413 and t <= 415:
            MASTER_OFFSET_TABLE[t][0] = 2 * t - 783
        elif t >= 415 and t <= 419:
            MASTER_OFFSET_TABLE[t][0] = 47
        elif t >= 419 and t <= 420:
            MASTER_OFFSET_TABLE[t][0] = t - 372
        elif t >= 420 and t <= 540:
            MASTER_OFFSET_TABLE[t][0] = 0.308*t - 81.5
        elif t >= 540 and t <= 600:
            MASTER_OFFSET_TABLE[t][0] = 0.35 * t - 104
        elif t >= 600 and t <= 660:
            MASTER_OFFSET_TABLE[t][0] = 0.4 * t - 134
        elif t >= 660 and t <= 720:
            MASTER_OFFSET_TABLE[t][0] = 0.283*t -57
        elif t >= 720 and t <= 840:
            MASTER_OFFSET_TABLE[t][0] = -0.05*t +183
        elif t >= 840 and t <= 900:
            MASTER_OFFSET_TABLE[t][0] = -0.0167*t+155
        elif t >= 900 and t <= 960:
            MASTER_OFFSET_TABLE[t][0] = 140
        elif t >= 960 and t <= 1020:
            MASTER_OFFSET_TABLE[t][0] = -0.033*t +172
        elif t >= 1020 and t <= 1080:
            MASTER_OFFSET_TABLE[t][0] = 138
        elif t >= 1080 and t <= 1140:
            MASTER_OFFSET_TABLE[t][0] = -0.1167*t +264
        elif t >= 1140 and t <= 1142:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2422
        elif t >= 1142 and t <= 1146:
            MASTER_OFFSET_TABLE[t][0] = -t + 1280
        elif t >= 1146 and t <= 1148:
            MASTER_OFFSET_TABLE[t][0] = 134
        elif t >= 1148 and t <= 1150:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 708
        elif t >= 1150 and t <= 1152:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2433
        elif t >= 1152 and t <= 1154:
            MASTER_OFFSET_TABLE[t][0] = 129
        elif t >= 1154 and t <= 1156:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2437
        elif t >= 1156 and t <= 1158:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 703
        elif t >= 1158 and t <= 1160:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2440
        elif t >= 1160 and t <= 1164:
            MASTER_OFFSET_TABLE[t][0] = 120
        elif t >= 1164 and t <= 1166:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3030
        elif t >= 1166 and t <= 1168:
            MASTER_OFFSET_TABLE[t][0] = 115
        elif t >= 1168 and t <= 1170:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2451
        elif t >= 1170 and t <= 1172:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 696
        elif t >= 1172 and t <= 1174:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2454
        elif t >= 1174 and t <= 1176:
            MASTER_OFFSET_TABLE[t][0] = 106
        elif t >= 1176 and t <= 1178:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 694
        elif t >= 1178 and t <= 1180:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2461
        elif t >= 1180 and t <= 1182:
            MASTER_OFFSET_TABLE[t][0] = 101
        elif t >= 1182 and t <= 1184:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2465
        elif t >= 1184 and t <= 1186:
            MASTER_OFFSET_TABLE[t][0] = 97
        elif t >= 1186 and t <= 1188:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 690
        elif t >= 1188 and t <= 1190:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1878
        elif t >= 1190 and t <= 1192:
            MASTER_OFFSET_TABLE[t][0] = 93
        elif t >= 1192 and t <= 1194:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3073
        elif t >= 1194 and t <= 1198:
            MASTER_OFFSET_TABLE[t][0] = 88
        elif t >= 1198 and t <= 1200:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2484
        elif t >= 1200 and t <= 1202:
            MASTER_OFFSET_TABLE[t][0] = 84
        elif t >= 1202 and t <= 1204:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3089
        elif t >= 1204 and t <= 1206:
            MASTER_OFFSET_TABLE[t][0] = 79
        elif t >= 1206 and t <= 1208:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2491
        elif t >= 1208 and t <= 1210:
            MASTER_OFFSET_TABLE[t][0] = 75
        elif t >= 1210 and t <= 1212:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 680
        elif t >= 1212 and t <= 1214:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1892
        elif t >= 1214 and t <= 1216:
            MASTER_OFFSET_TABLE[t][0] = 71
        elif t >= 1216 and t <= 1218:
            MASTER_OFFSET_TABLE[t][0] = -2 * t + 2503
        elif t >= 1218 and t <= 1222:
            MASTER_OFFSET_TABLE[t][0] = 67
        elif t >= 1222 and t <= 1224:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3122
        elif t >= 1224 and t <= 1226:
            MASTER_OFFSET_TABLE[t][0] = 62
        elif t >= 1226 and t <= 1228:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1901
        elif t >= 1228 and t <= 1232:
            MASTER_OFFSET_TABLE[t][0] = 59
        elif t >= 1232 and t <= 1234:
            MASTER_OFFSET_TABLE[t][0] = -2.5 * t + 3139
        elif t >= 1234 and t <= 1236:
            MASTER_OFFSET_TABLE[t][0] = 54
        elif t >= 1236 and t <= 1238:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1908
        elif t >= 1238 and t <= 1240:
            MASTER_OFFSET_TABLE[t][0] = 51
        elif t >= 1240 and t <= 1242:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 671
        elif t >= 1242 and t <= 1244:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1913
        elif t >= 1244 and t <= 1246:
            MASTER_OFFSET_TABLE[t][0] = 47
        elif t >= 1246 and t <= 1248:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1916
        elif t >= 1248 and t <= 1250:
            MASTER_OFFSET_TABLE[t][0] = 44
        elif t >= 1250 and t <= 1252:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1919
        elif t >= 1252 and t <= 1254:
            MASTER_OFFSET_TABLE[t][0] = 41
        elif t >= 1254 and t <= 1256:
            MASTER_OFFSET_TABLE[t][0] = -1.5 * t + 1922
        elif t >= 1256 and t <= 1258:
            MASTER_OFFSET_TABLE[t][0] = 38
        elif t >= 1258 and t <= 1260:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 667
        elif t >= 1260 and t <= 1262:
            MASTER_OFFSET_TABLE[t][0] = -t * 1297
        elif t >= 1262 and t <= 1264:
            MASTER_OFFSET_TABLE[t][0] = 35
        elif t >= 1264 and t <= 1266:
            MASTER_OFFSET_TABLE[t][0] = -t + 1299
        elif t >= 1266 and t <= 1268:
            MASTER_OFFSET_TABLE[t][0] = 33
        elif t >= 1268 and t <= 1270:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 667
        elif t >= 1270 and t <= 1272:
            MASTER_OFFSET_TABLE[t][0] = -t + 1302
        elif t >= 1272 and t <= 1274:
            MASTER_OFFSET_TABLE[t][0] = 30
        elif t >= 1274 and t <= 1276:
            MASTER_OFFSET_TABLE[t][0] = -t + 1304
        elif t >= 1276 and t <= 1278:
            MASTER_OFFSET_TABLE[t][0] = 28
        elif t >= 1278 and t <= 1282:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 667
        elif t >= 1282 and t <= 1284:
            MASTER_OFFSET_TABLE[t][0] = 26
        elif t >= 1284 and t <= 1286:
            MASTER_OFFSET_TABLE[t][0] = -t + 1310
        elif t >= 1286 and t <= 1290:
            MASTER_OFFSET_TABLE[t][0] = 24
        elif t >= 1290 and t <= 1292:
            MASTER_OFFSET_TABLE[t][0] = -t + 1314
        elif t >= 1292 and t <= 1296:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 668
        elif t >= 1296 and t <= 1298:
            MASTER_OFFSET_TABLE[t][0] = 20
        elif t >= 1298 and t <= 1302:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 669
        elif t >= 1302 and t <= 1304:
            MASTER_OFFSET_TABLE[t][0] = 18
        elif t >= 1304 and t <= 1306:
            MASTER_OFFSET_TABLE[t][0] = -t + 1322
        elif t >= 1306 and t <= 1308:
            MASTER_OFFSET_TABLE[t][0] = 16
        elif t >= 1308 and t <= 1310:
            MASTER_OFFSET_TABLE[t][0] = -t + 1324
        elif t >= 1310 and t <= 1314:
            MASTER_OFFSET_TABLE[t][0] = 14
        elif t >= 1314 and t <= 1316:
            MASTER_OFFSET_TABLE[t][0] = -t + 1328
        elif t >= 1316 and t <= 1318:
            MASTER_OFFSET_TABLE[t][0] = 12
        elif t >= 1318 and t <= 1320:
            MASTER_OFFSET_TABLE[t][0] = -t + 1330
        elif t >= 1320 and t <= 1324:
            MASTER_OFFSET_TABLE[t][0] = 10
        elif t >= 1324 and t <= 1326:
            MASTER_OFFSET_TABLE[t][0] = -t + 1334
        elif t >= 1326 and t <= 1328:
            MASTER_OFFSET_TABLE[t][0] = 8
        elif t >= 1328 and t <= 1330:
            MASTER_OFFSET_TABLE[t][0] = -t + 1336
        elif t >= 1330 and t <= 1334:
            MASTER_OFFSET_TABLE[t][0] = 6
        elif t >= 1334 and t <= 1340:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 673
        elif t >= 1340 and t <= 1342:
            MASTER_OFFSET_TABLE[t][0] = 3
        elif t >= 1342 and t <= 1344:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 674
        elif t >= 1344 and t <= 1348:
            MASTER_OFFSET_TABLE[t][0] = 2
        elif t >= 1348 and t <= 1350:
            MASTER_OFFSET_TABLE[t][0] = -0.5 * t + 676
        else:
            MASTER_OFFSET_TABLE[t][0] = 0
        t += 1
    return MASTER_OFFSET_TABLE


def init_green_offset(MASTER_OFFSET_TABLE):
    #global MASTER_OFFSET_TABLE
    t = 0
    #print "INIT GREEN"
    while t < 1440:
        if t >= 313 and t <= 315:
            MASTER_OFFSET_TABLE[t][1] = 0
        elif t >= 315 and t <= 323:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 157.5
        elif t >= 323 and t <= 325:
            MASTER_OFFSET_TABLE[t][1] = 4
        elif t >= 325 and t <= 327:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 158
        elif t >= 327 and t <= 329:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 322
        elif t >= 329 and t <= 331:
            MASTER_OFFSET_TABLE[t][1] = 7
        elif t >= 331 and t <= 333:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 158
        elif t >= 333 and t <= 335:
            MASTER_OFFSET_TABLE[t][1] = t - 325
        elif t >= 335 and t <= 337:
            MASTER_OFFSET_TABLE[t][1] = 10
        elif t >= 337 and t <= 341:
            MASTER_OFFSET_TABLE[t][1] = t - 327
        elif t >= 341 and t <= 343:
            MASTER_OFFSET_TABLE[t][1] = 14
        elif t >= 343 and t <= 345:
            MASTER_OFFSET_TABLE[t][1] = t - 329
        elif t >= 345 and t <= 351:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 156.5
        elif t >= 351 and t <= 353:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 507.5
        elif t >= 353 and t <= 357:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 154.5
        elif t >= 357 and t <= 359:
            MASTER_OFFSET_TABLE[t][1] = t - 33
        elif t >= 359 and t <= 361:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 512.5
        elif t >= 361 and t <= 363:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 151.5
        elif t >= 363 and t <= 365:
            MASTER_OFFSET_TABLE[t][1] = t - 333
        elif t >= 365 and t <= 367:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 150.5
        elif t >= 367 and t <= 369:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 701
        elif t >= 369 and t <= 371:
            MASTER_OFFSET_TABLE[t][1] = 37
        elif t >= 371 and t <= 375:
            MASTER_OFFSET_TABLE[t][1] = t - 334
        elif t >= 375 and t <= 377:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 521.5
        elif t >= 377 and t <= 379:
            MASTER_OFFSET_TABLE[t][1] = t - 333
        elif t >= 379 and t <= 381:
            MASTER_OFFSET_TABLE[t][1] = 46
        elif t >= 381 and t <= 383:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 525.5
        elif t >= 383 and t <= 385:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 717
        elif t >= 385 and t <= 389:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 139.5
        elif t >= 389 and t <= 391:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 528.5
        elif t >= 391 and t <= 393:
            MASTER_OFFSET_TABLE[t][1] = t - 333
        elif t >= 393 and t <= 395:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 529.5
        elif t >= 395 and t <= 397:
            MASTER_OFFSET_TABLE[t][1] = t - 332
        elif t >= 397 and t <= 399:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 729
        elif t >= 399 and t <= 401:
            MASTER_OFFSET_TABLE[t][1] = 69
        elif t >= 401 and t <= 403:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 733
        elif t >= 403 and t <= 405:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 128.5
        elif t >= 405 and t <= 407:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 533.5
        elif t >= 407 and t <= 409:
            MASTER_OFFSET_TABLE[t][1] = t - 330
        elif t >= 409 and t <= 411:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 125.5
        elif t >= 411 and t <= 413:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 536.5
        elif t >= 413 and t <= 415:
            MASTER_OFFSET_TABLE[t][1] = 2 * t - 743
        elif t >= 415 and t <= 417:
            MASTER_OFFSET_TABLE[t][1] = 0.5 * t - 120.5
        elif t >= 417 and t <= 419:
            MASTER_OFFSET_TABLE[t][1] = 1.5 * t - 537.5
        elif t >= 419 and t <= 420:
            MASTER_OFFSET_TABLE[t][1] = t - 328
        elif t >= 420 and t <= 720:
            MASTER_OFFSET_TABLE[t][1] = 0.097 * t + 51.4
        elif t >= 720 and t <= 780:
            MASTER_OFFSET_TABLE[t][1] = -0.3 *t +336
        elif t >= 780 and t <= 840:
            MASTER_OFFSET_TABLE[t][1] = -0.25 *t +297
        elif t >= 840 and t <= 900:
            MASTER_OFFSET_TABLE[t][1] = -0.233 * t + 283
        elif t >= 900 and t <= 960:
            MASTER_OFFSET_TABLE[t][1] = -0.25*t +298
        elif t >= 960 and t <= 1080:
            MASTER_OFFSET_TABLE[t][1] = -0.2 * t + 250
        elif t >= 1080 and t <= 1140:
            MASTER_OFFSET_TABLE[t][1] = -0.133 * t + 178
        elif t >= 1140 and t <= 1146:
            MASTER_OFFSET_TABLE[t][1] = 28
        elif t >= 1146 and t <= 1148:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 601
        elif t >= 1148 and t <= 1150:
            MASTER_OFFSET_TABLE[t][1] = 27
        elif t >= 1150 and t <= 1152:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 602
        elif t >= 1152 and t <= 1154:
            MASTER_OFFSET_TABLE[t][1] = 26
        elif t >= 1154 and t <= 1156:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 603
        elif t >= 1156 and t <= 1164:
            MASTER_OFFSET_TABLE[t][1] = 25
        elif t >= 1164 and t <= 1166:
            MASTER_OFFSET_TABLE[t][1] = -t * +1189
        elif t >= 1166 and t <= 1172:
            MASTER_OFFSET_TABLE[t][1] = 23
        elif t >= 1172 and t <= 1174:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 609
        elif t >= 1174 and t <= 1178:
            MASTER_OFFSET_TABLE[t][1] = 22
        elif t >= 1178 and t <= 1182:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 611
        elif t >= 1182 and t <= 1194:
            MASTER_OFFSET_TABLE[t][1] = 20
        elif t >= 1194 and t <= 1198:
            MASTER_OFFSET_TABLE[t][1] = 18
        elif t >= 1198 and t <= 1200:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 617
        elif t >= 1200 and t <= 1202:
            MASTER_OFFSET_TABLE[t][1] = 17
        elif t >= 1202 and t <= 1204:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 618
        elif t >= 1204 and t <= 1210:
            MASTER_OFFSET_TABLE[t][1] = 16
        elif t >= 1210 and t <= 1212:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 621
        elif t >= 1212 and t <= 1216:
            MASTER_OFFSET_TABLE[t][1] = 15
        elif t >= 1216 and t <= 1218:
            MASTER_OFFSET_TABLE[t][1] = -t + 1231
        elif t >= 1218 and t <= 1226:
            MASTER_OFFSET_TABLE[t][1] = 13
        elif t >= 1226 and t <= 1230:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 626
        elif t >= 1230 and t <= 1238:
            MASTER_OFFSET_TABLE[t][1] = 11
        elif t >= 1238 and t <= 1240:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 630
        elif t >= 1240 and t <= 1242:
            MASTER_OFFSET_TABLE[t][1] = 10
        elif t >= 1242 and t <= 1244:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 631
        elif t >= 1244 and t <= 1250:
            MASTER_OFFSET_TABLE[t][1] = 9
        elif t >= 1250 and t <= 1252:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 634
        elif t >= 1252 and t <= 1254:
            MASTER_OFFSET_TABLE[t][1] = 8
        elif t >= 1254 and t <= 1256:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 635
        elif t >= 1256 and t <= 1264:
            MASTER_OFFSET_TABLE[t][1] = 7
        elif t >= 1264 and t <= 1266:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 639
        elif t >= 1266 and t <= 1268:
            MASTER_OFFSET_TABLE[t][1] = 6
        elif t >= 1268 and t <= 1270:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 640
        elif t >= 1270 and t <= 1280:
            MASTER_OFFSET_TABLE[t][1] = 5
        elif t >= 1280 and t <= 1282:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 645
        elif t >= 1282 and t <= 1290:
            MASTER_OFFSET_TABLE[t][1] = 4
        elif t >= 1290 and t <= 1292:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 649
        elif t >= 1292 and t <= 1298:
            MASTER_OFFSET_TABLE[t][1] = 3
        elif t >= 1298 and t <= 1300:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 652
        elif t >= 1300 and t <= 1308:
            MASTER_OFFSET_TABLE[t][1] = 2
        elif t >= 1308 and t <= 1310:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 656
        elif t >= 1310 and t <= 1328:
            MASTER_OFFSET_TABLE[t][1] = 1
        elif t >= 1328 and t <= 1330:
            MASTER_OFFSET_TABLE[t][1] = -0.5 * t + 665
        else:
            MASTER_OFFSET_TABLE[t][1] = 0

        t += 1
    return MASTER_OFFSET_TABLE

def init_blue_offset(MASTER_OFFSET_TABLE):
    #global MASTER_OFFSET_TABLE
    t = 0
    while t < 1440:
        if t >= 313 and t <= 319:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 165.5
        elif t >= 319 and t <= 321:
            MASTER_OFFSET_TABLE[t][2] = t - 316
        elif t >= 321 and t <= 323:
            MASTER_OFFSET_TABLE[t][2] = 5
        elif t >= 323 and t <= 325:
            MASTER_OFFSET_TABLE[t][2] = t - 318
        elif t >= 325 and t <= 327:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 155.5
        elif t >= 327 and t <= 329:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 482.5
        elif t >= 329 and t <= 333:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 153.5
        elif t >= 333 and t <= 335:
            MASTER_OFFSET_TABLE[t][2] = t - 320
        elif t >= 335 and t <= 337:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 152.5
        elif t >= 337 and t <= 339:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 489.5
        elif t >= 339 and t <= 341:
            MASTER_OFFSET_TABLE[t][2] = t - 320
        elif t >= 341 and t <= 345:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 149.5
        elif t >= 345 and t <= 347:
            MASTER_OFFSET_TABLE[t][2] = t - 322
        elif t >= 347 and t <= 349:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 495.5
        elif t >= 349 and t <= 351:
            MASTER_OFFSET_TABLE[t][2] = t - 321
        elif t >= 351 and t <= 353:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 847.5
        elif t >= 353 and t <= 355:
            MASTER_OFFSET_TABLE[t][2] = 35
        elif t >= 355 and t <= 357:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 497.5
        elif t >= 357 and t <= 365:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 676
        elif t >= 365 and t <= 367:
            MASTER_OFFSET_TABLE[t][2] = 54
        elif t >= 367 and t <= 369:
            MASTER_OFFSET_TABLE[t][2] = 4 * t - 1414
        elif t >= 369 and t <= 371:
            MASTER_OFFSET_TABLE[t][2] = t - 122.5
        elif t >= 371 and t <= 373:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 493.5
        elif t >= 373 and t <= 375:
            MASTER_OFFSET_TABLE[t][2] = 3 * t - 1053
        elif t >= 375 and t <= 377:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 865.5
        elif t >= 377 and t <= 379:
            MASTER_OFFSET_TABLE[t][2] = 0.5 * t - 111.5
        elif t >= 379 and t <= 383:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 688
        elif t >= 383 and t <= 385:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 871.5
        elif t >= 385 and t <= 387:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 679
        elif t >= 387 and t <= 389:
            MASTER_OFFSET_TABLE[t][2] = t - 292
        elif t >= 389 and t <= 391:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 681
        elif t >= 391 and t <= 397:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 876.5
        elif t >= 397 and t <= 399:
            MASTER_OFFSET_TABLE[t][2] = 3 * t - 1075
        elif t >= 399 and t <= 401:
            MASTER_OFFSET_TABLE[t][2] = 122
        elif t >= 401 and t <= 403:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 680
        elif t >= 403 and t <= 405:
            MASTER_OFFSET_TABLE[t][2] = 3 * t - 1083
        elif t >= 405 and t <= 407:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 475.5
        elif t >= 407 and t <= 409:
            MASTER_OFFSET_TABLE[t][2] = 3.5 * t - 1289.5
        elif t >= 409 and t <= 411:
            MASTER_OFFSET_TABLE[t][2] = 142
        elif t >= 411 and t <= 413:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 680
        elif t >= 413 and t <= 415:
            MASTER_OFFSET_TABLE[t][2] = 3.5 * t - 1299.5
        elif t >= 415 and t <= 417:
            MASTER_OFFSET_TABLE[t][2] = 2.5 * t - 884.5
        elif t >= 417 and t <= 419:
            MASTER_OFFSET_TABLE[t][2] = 1.5 * t - 467.5
        elif t >= 419 and t <= 420:
            MASTER_OFFSET_TABLE[t][2] = 2 * t - 677
        elif t >= 420 and t <= 720:
            MASTER_OFFSET_TABLE[t][2] = 0.103 * t + 117.6
        elif t >= 720 and t <= 780:
            MASTER_OFFSET_TABLE[t][2] = -0.467 * t + 526
        elif t >= 780 and t <= 840:
            MASTER_OFFSET_TABLE[t][2] = -0.4*t+474
        elif t >= 840 and t <= 900:
            MASTER_OFFSET_TABLE[t][2] = -0.4167 * t + 488
        elif t >= 900 and t <= 960:
            MASTER_OFFSET_TABLE[t][2] = -0.4*t+473
        elif t >= 960 and t <= 1020:
            MASTER_OFFSET_TABLE[t][2] = -0.367 * t + 441
        elif t >= 1020 and t <= 1080:
            MASTER_OFFSET_TABLE[t][2] = -0.3*t+373
        elif t >= 1080 and t <= 1140:
            MASTER_OFFSET_TABLE[t][2] = -0.2 * t + 265
        elif t >= 1140 and t <= 1142:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 612
        elif t >= 1142 and t <= 1144:
            MASTER_OFFSET_TABLE[t][2] = 41
        elif t >= 1144 and t <= 1146:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 613
        elif t >= 1146 and t <= 1150:
            MASTER_OFFSET_TABLE[t][2] = 40
        elif t >= 1150 and t <= 1152:
            MASTER_OFFSET_TABLE[t][2] = -t + 1190
        elif t >= 1152 and t <= 1154:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 614
        elif t >= 1154 and t <= 1158:
            MASTER_OFFSET_TABLE[t][2] = 37
        elif t >= 1158 and t <= 1160:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 616
        elif t >= 1160 and t <= 1164:
            MASTER_OFFSET_TABLE[t][2] = 36
        elif t >= 1164 and t <= 1166:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 618
        elif t >= 1166 and t <= 1168:
            MASTER_OFFSET_TABLE[t][2] = -t + 1201
        elif t >= 1168 and t <= 1172:
            MASTER_OFFSET_TABLE[t][2] = 33
        elif t >= 1172 and t <= 1174:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 619
        elif t >= 1174 and t <= 1178:
            MASTER_OFFSET_TABLE[t][2] = 32
        elif t >= 1178 and t <= 1180:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 621
        elif t >= 1180 and t <= 1182:
            MASTER_OFFSET_TABLE[t][2] = -t + 1211
        elif t >= 1182 and t <= 1188:
            MASTER_OFFSET_TABLE[t][2] = 29
        elif t >= 1188 and t <= 1192:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 623
        elif t >= 1192 and t <= 1194:
            MASTER_OFFSET_TABLE[t][2] = 27
        elif t >= 1194 and t <= 1196:
            MASTER_OFFSET_TABLE[t][2] = -t + 1221
        elif t >= 1196 and t <= 1202:
            MASTER_OFFSET_TABLE[t][2] = 25
        elif t >= 1202 and t <= 1204:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 626
        elif t >= 1204 and t <= 1206:
            MASTER_OFFSET_TABLE[t][2] = 24
        elif t >= 1206 and t <= 1208:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 627
        elif t >= 1208 and t <= 1210:
            MASTER_OFFSET_TABLE[t][2] = 23
        elif t >= 1210 and t <= 1212:
            MASTER_OFFSET_TABLE[t][2] = -t + 1233
        elif t >= 1212 and t <= 1216:
            MASTER_OFFSET_TABLE[t][2] = 21
        elif t >= 1216 and t <= 1218:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 629
        elif t >= 1218 and t <= 1222:
            MASTER_OFFSET_TABLE[t][2] = 20
        elif t >= 1222 and t <= 1228:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 631
        elif t >= 1228 and t <= 1230:
            MASTER_OFFSET_TABLE[t][2] = 30
        elif t >= 1230 and t <= 1232:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 632
        elif t >= 1232 and t <= 1236:
            MASTER_OFFSET_TABLE[t][2] = 16
        elif t >= 1236 and t <= 1240:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 634
        elif t >= 1240 and t <= 1242:
            MASTER_OFFSET_TABLE[t][2] = 14
        elif t >= 1242 and t <= 1244:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 635
        elif t >= 1244 and t <= 1246:
            MASTER_OFFSET_TABLE[t][2] = 13
        elif t >= 1246 and t <= 1248:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 636
        elif t >= 1248 and t <= 1254:
            MASTER_OFFSET_TABLE[t][2] = 12
        elif t >= 1254 and t <= 1256:
            MASTER_OFFSET_TABLE[t][2] = -t + 1266
        elif t >= 1256 and t <= 1262:
            MASTER_OFFSET_TABLE[t][2] = 10
        elif t >= 1262 and t <= 1264:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 641
        elif t >= 1264 and t <= 1268:
            MASTER_OFFSET_TABLE[t][2] = 9
        elif t >= 1268 and t <= 1272:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 643
        elif t >= 1272 and t <= 1280:
            MASTER_OFFSET_TABLE[t][2] = 7
        elif t >= 1280 and t <= 1282:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 647
        elif t >= 1282 and t <= 1284:
            MASTER_OFFSET_TABLE[t][2] = 6
        elif t >= 1284 and t <= 1286:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 648
        elif t >= 1286 and t <= 1294:
            MASTER_OFFSET_TABLE[t][2] = 5
        elif t >= 1294 and t <= 1296:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 652
        elif t >= 1296 and t <= 1298:
            MASTER_OFFSET_TABLE[t][2] = 4
        elif t >= 1298 and t <= 1300:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 653
        elif t >= 1300 and t <= 1308:
            MASTER_OFFSET_TABLE[t][2] = 3
        elif t >= 1308 and t <= 1310:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 657
        elif t >= 1310 and t <= 1320:
            MASTER_OFFSET_TABLE[t][2] = 2
        elif t >= 1320 and t <= 1322:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 662
        elif t >= 1322 and t <= 1338:
            MASTER_OFFSET_TABLE[t][2] = 1
        elif t >= 1338 and t <= 1340:
            MASTER_OFFSET_TABLE[t][2] = -0.5 * t + 670
        else:
            MASTER_OFFSET_TABLE[t][2] = 0

        t += 1
    return MASTER_OFFSET_TABLE

def init_master_lux_table():
    #global MASTER_LUX_TABLE
    MASTER_LUX_TABLE = []
    t = 0
    while t < 1440:
        MASTER_LUX_TABLE.append(0)
        t += 1
    t = 0
    while t < 1440:
        if t >= 313 and t <= 319:
            MASTER_LUX_TABLE[t] = 0
        elif t >= 319 and t <= 321:
            MASTER_LUX_TABLE[t] = 0.5 * t - 159.5
        elif t >= 321 and t <= 325:
            MASTER_LUX_TABLE[t] = 1
        elif t >= 325 and t <= 327:
            MASTER_LUX_TABLE[t] = 0.5 * t - 161.5
        elif t >= 327 and t <= 335:
            MASTER_LUX_TABLE[t] = 2
        elif t >= 335 and t <= 337:
            MASTER_LUX_TABLE[t] = 0.5 * t - 165.5
        elif t >= 337 and t <= 343:
            MASTER_LUX_TABLE[t] = 3
        elif t >= 343 and t <= 345:
            MASTER_LUX_TABLE[t] = 0.5 * t - 168.5
        elif t >= 345 and t <= 349:
            MASTER_LUX_TABLE[t] = 4
        elif t >= 349 and t <= 351:
            MASTER_LUX_TABLE[t] = 0.5 * t - 170.5
        elif t >= 351 and t <= 353:
            MASTER_LUX_TABLE[t] = 5
        elif t >= 353 and t <= 355:
            MASTER_LUX_TABLE[t] = 0.5 * t - 171.5
        elif t >= 355 and t <= 359:
            MASTER_LUX_TABLE[t] = 6
        elif t >= 359 and t <= 361:
            MASTER_LUX_TABLE[t] = 0.5 * t - 173.5
        elif t >= 361 and t <= 363:
            MASTER_LUX_TABLE[t] = 7
        elif t >= 363 and t <= 365:
            MASTER_LUX_TABLE[t] = 0.5 * t - 174.5
        elif t >= 365 and t <= 369:
            MASTER_LUX_TABLE[t] = 8
        elif t >= 369 and t <= 373:
            MASTER_LUX_TABLE[t] = 0.5 * t - 176.5
        elif t >= 373 and t <= 377:
            MASTER_LUX_TABLE[t] = 10
        elif t >= 377 and t <= 379:
            MASTER_LUX_TABLE[t] = 0.5 * t - 178.5
        elif t >= 379 and t <= 381:
            MASTER_LUX_TABLE[t] = 11
        elif t >= 381 and t <= 385:
            MASTER_LUX_TABLE[t] = 0.5 * t - 179.5
        elif t >= 385 and t <= 389:
            MASTER_LUX_TABLE[t] = 13
        elif t >= 389 and t <= 393:
            MASTER_LUX_TABLE[t] = 0.5 * t - 181.5
        elif t >= 393 and t <= 397:
            MASTER_LUX_TABLE[t] = 15
        elif t >= 397 and t <= 401:
            MASTER_LUX_TABLE[t] = 0.5 * t - 183.5
        elif t >= 401 and t <= 403:
            MASTER_LUX_TABLE[t] = 17
        elif t >= 403 and t <= 405:
            MASTER_LUX_TABLE[t] = 0.5 * t - 184.5
        elif t >= 405 and t <= 407:
            MASTER_LUX_TABLE[t] = 18
        elif t >= 407 and t <= 409:
            MASTER_LUX_TABLE[t] = 0.5 * t - 185.5
        elif t >= 409 and t <= 411:
            MASTER_LUX_TABLE[t] = 19
        elif t >= 411 and t <= 415:
            MASTER_LUX_TABLE[t] = 0.5 * t - 186.5
        elif t >= 415 and t <= 420:
            MASTER_LUX_TABLE[t] = 21
        elif t >= 420 and t <= 720:
            MASTER_LUX_TABLE[t] = 0.023 * t + 11.2
        elif t >= 720 and t <= 1140:
            MASTER_LUX_TABLE[t] = -0.0452 * t + 60.57
        elif t >= 1140 and t <= 1142:
            MASTER_LUX_TABLE[t] = -0.5 * t + 579
        elif t >= 1142 and t <= 1152:
            MASTER_LUX_TABLE[t] = 8
        elif t >= 1152 and t <= 1154:
            MASTER_LUX_TABLE[t] = -0.5 * t + 584
        elif t >= 1154 and t <= 1164:
            MASTER_LUX_TABLE[t] = 7
        elif t >= 1164 and t <= 1166:
            MASTER_LUX_TABLE[t] = -0.5 * t + 589
        elif t >= 1166 and t <= 1180:
            MASTER_LUX_TABLE[t] = 6
        elif t >= 1180 and t <= 1182:
            MASTER_LUX_TABLE[t] = -0.5 * t + 596
        elif t >= 1182 and t <= 1196:
            MASTER_LUX_TABLE[t] = 5
        elif t >= 1196 and t <= 1198:
            MASTER_LUX_TABLE[t] = -0.5 * t + 603
        elif t >= 1198 and t <= 1214:
            MASTER_LUX_TABLE[t] = 4
        elif t >= 1214 and t <= 1216:
            MASTER_LUX_TABLE[t] = -0.5 * t + 611
        elif t >= 1216 and t <= 1230:
            MASTER_LUX_TABLE[t] = 3
        elif t >= 1230 and t <= 1232:
            MASTER_LUX_TABLE[t] = -0.5 * t + 618
        elif t >= 1232 and t <= 1258:
            MASTER_LUX_TABLE[t] = 2
        elif t >= 1258 and t <= 1260:
            MASTER_LUX_TABLE[t] = -0.5 * t + 631
        elif t >= 1260 and t <= 1292:
            MASTER_LUX_TABLE[t] = 1
        elif t >= 1292 and t <= 1294:
            MASTER_LUX_TABLE[t] = -0.5 * t + 647
        else:
            MASTER_LUX_TABLE[t] = 0
        t += 1
    return MASTER_LUX_TABLE

def calc_user_tables(WAKE_UP_TIME, MASTER_CIRCADIAN_TABLE, MASTER_OFFSET_TABLE, MASTER_LUX_TABLE):
    """
    This function calculates the user's circadian table for the room
    that the Raspberry Pi will be in. Depending on when the user's
    wake up time is, the MASTER_CIRCADIAN_TABLE will be shifted. If the
    user's wake up time is earlier than 7 AM, then the USER_CIRCADIAN_TABLE
    will hold the MASTER_CIRCADIAN_TABLE shifted to the left. If the user
    wakes up later than 7 AM, then the USER_CIRCADIAN_TABLE will hold the
    MASTER_CIRCADIAN_TABLE shifted to the right. Lastly, if the user wakes up
    exactly at 7 AM, then the USER_CIRCADIAN_TABLE will exactly be the
    MASTER_CIRCADIAN_TABLE.

    :param change_par_Event: A threading event when user changed any
    circadian parameter.

    :param finalize_change_Event: A threading event for finalizing the
    change that the user made.

    :return: None.
    """

    """
    When calculating the USER_CIRCADIAN_TABLE again,
    the past values must be cleared but must have the
    same length as the MASTER_CIRCADIAN_TABLE. So, set
    the USER_CIRCADIAN_TABLE to the MASTER_CIRCADIAN_TABLE.
    """

    USER_CIRCADIAN_TABLE = MASTER_CIRCADIAN_TABLE[:]
    USER_OFFSET_TABLE = MASTER_OFFSET_TABLE[:]
    USER_LUX_TABLE = MASTER_LUX_TABLE[:]

    """
    Calculate if user wakes up earlier or later than 7 AM
    """
    wake_diff = WAKE_UP_TIME - 420
    count = 0
    if wake_diff < 0:
        """
        User wakes earlier than 7 AM
        """
        while count < 1440:
            USER_CIRCADIAN_TABLE[count + wake_diff] = MASTER_CIRCADIAN_TABLE[count]
            USER_OFFSET_TABLE[count + wake_diff] = MASTER_OFFSET_TABLE[count]
            USER_LUX_TABLE[count + wake_diff] = MASTER_LUX_TABLE[count]
            count += 1
    elif wake_diff > 0:
        """
        User wakes up later than 7 AM
        """
        while count < 1440:

            if (count + wake_diff) > 1439:
                """
                For later indexes in the list, the values must wrap around
                to earlier indexes. Therefore, take the MOD.
                """
                USER_CIRCADIAN_TABLE[(count + wake_diff) % 1440] = MASTER_CIRCADIAN_TABLE[count]
                USER_OFFSET_TABLE[(count + wake_diff) % 1440] = MASTER_OFFSET_TABLE[count]
                USER_LUX_TABLE[(count + wake_diff) % 1440] = MASTER_LUX_TABLE[count]
            else:
                USER_CIRCADIAN_TABLE[count + wake_diff] = MASTER_CIRCADIAN_TABLE[count]
                USER_OFFSET_TABLE[count + wake_diff] = MASTER_OFFSET_TABLE[count]
                USER_LUX_TABLE[count + wake_diff] = MASTER_LUX_TABLE[count]
            count += 1
    """
    Return tuple of user tables
    """
    return (USER_CIRCADIAN_TABLE, USER_OFFSET_TABLE, USER_LUX_TABLE)

def get_pids():
    result = []
    pir_sensor_pid = subprocess.check_output(['pgrep', '-f', 'pir_sensor.py'])
    pir_sensor_pid = pir_sensor_pid.split('\n')
    pir_sensor_pid = int(pir_sensor_pid[0])
    rgb_sensor_pid = subprocess.check_output(['pgrep', '-f', 'rgb_sensor.py'])
    rgb_sensor_pid = rgb_sensor_pid.split('\n')
    rgb_sensor_pid = int(rgb_sensor_pid[0])
    usr_sensor_pid = subprocess.check_output(['pgrep', '-f', 'usr_sensor.py'])
    usr_sensor_pid = usr_sensor_pid.split('\n')
    usr_sensor_pid = int(usr_sensor_pid[0])
    wait_for_cmd_pid = subprocess.check_output(['pgrep', '-f', 'wait_for_cmd.py'])
    wait_for_cmd_pid = wait_for_cmd_pid.split('\n')
    wait_for_cmd_pid = int(wait_for_cmd_pid[0])
    send_circadian_pid = subprocess.check_output(['pgrep', '-f', 'send_circadian_values.py'])
    send_circadian_pid = send_circadian_pid.split('\n')
    send_circadian_pid = int(send_circadian_pid[0])
    result.append(pir_sensor_pid)
    result.append(rgb_sensor_pid)
    result.append(usr_sensor_pid)
    result.append(wait_for_cmd_pid)
    result.append(send_circadian_pid)
    return result

def get_ip():
    """
    This function is used to get the local IP address of the Raspberry Pi.

    :return: The local IP address.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def execute_dB_query(cursor, db, sql, sql_args):
    if sql[0] != 'S' and sql[0] != 's':
        """
        Query is something other than select query
        """
        try:
            if len(sql_args) == 0:
                cursor.execute(sql)
            else:
                cursor.execute(sql, sql_args)
            db.commit()
        except (AttributeError, MySQLdb.OperationalError):
            print "Re-establishing database connection in main thread..."
            db = MySQLdb.connect(host="192.168.1.6", port=3306, user="spatiumlucis", passwd="spatiumlucis",
                                 db="ilcs")
            print "Database connection re-established in main thread."
            cursor = db.cursor()
            try:
                if len(sql_args) == 0:
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, sql_args)
                db.commit()
            except:
                db.rollback()
        except:
            db.rollback()
    else:
        """
        query is select query
        """
        if len(sql_args) == 0:
            cursor.execute(sql)
        else:
            cursor.execute(sql, sql_args)
        result = cursor.fetchall()
        return result
