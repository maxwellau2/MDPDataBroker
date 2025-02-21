To Move forward: FWXXX
To Move backwards: BWXXX
To Move front left: A XXX
To Move front right: C XXX
XXX is the digit

# acknowledgement
{
    "from" : "stm",
    "msg" : {
        type: "ack",
    }
}

# Algo
will send the movements
{
    from: "algo",
    msg: {
        type: "path",
        data: [
            {s: 100},
            {l: 100},
            {r: 100},
            {s: -100}
        ]
    }
}
